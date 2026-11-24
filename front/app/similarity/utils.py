import os
import re
import zlib
from contextlib import closing

import numpy as np

import orjson
import requests
from collections import defaultdict
from itertools import combinations_with_replacement, islice

from pathlib import Path
from django.db import transaction
from django.db.models import Q, F, QuerySet, Value, Case, When
from django.db.models.functions import Coalesce

from app.similarity.const import SCORES_PATH
from app.config.settings import APP_URL, APP_NAME
from app.similarity.models.region_pair import (
    RegionPair,
    RegionPairTuple,
    parse_img,
    ImgRef,
    add_jpg,
)
from app.similarity.models.similarity_parameters import (
    SimilarityParameters,
)
from app.similarity import (
    SourceType,
    SIM_DEFAULTS,
    SimilarityType,
    Priority,
    SimilarityCategory,
)
from app.similarity.tasks import delete_api_similarity
from app.webapp.models.digitization import Digitization
from app.webapp.models.region_extraction import RegionExtraction, get_witness_ids
from app.webapp.models.witness import Witness
from app.webapp.utils import tasking
from app.webapp.utils.iiif import parse_ref
from app.webapp.utils.functions import delete_path, safe_float
from app.webapp.utils.logger import log
from app.similarity.dedupe import (
    fetch_distinct_images,
    close,
    parse_bbox,
    TYPE_PRIORITY,
    inherit_categories,
)
from app.webapp.utils.iiif.annotation import (
    has_annotation,
    get_canvas_annotations,
    get_coord_from_annotation,
)


################################################################
# ⚠️   prepare_request() & process_results() are mandatory  ⚠️ #
# ⚠️ function used by Treatment to generate request payload ⚠️ #
# ⚠️    and save results files when sends back by the API   ⚠️ #
################################################################


def prepare_request(witnesses, treatment_id, parameters=None):
    """
    Prepare similarity request:
    - document pairs already computed for these parameters are skipped, unless `force`
    - pairs_to_score() are sent to be scored one by one
    """
    params = similarity_param(parameters)
    uids = {doc["uid"] for w in witnesses for doc in prepare_document(w, **params)}
    computed = set() if params["force"] else get_existing_pairs(uids, params)
    pairs = (
        pairs_to_score(uids, similarity_hash(params), force=params["force"])
        if params["source_type"] == SourceType.REGIONS
        else []
    )
    if not pairs and computed and len(computed) == len(uids) * (len(uids) + 1) // 2:
        return {"message": "All similarity pairs already computed for these parameters"}

    return tasking.prepare_request(
        witnesses,
        treatment_id,
        prepare_document,
        "similarity",
        {**params, "skip_pairs": sorted(computed), "pairs": pairs},
    )


def pairs_to_score(wids: set[str], param_hash: str, force=False) -> list[list[str]]:
    """
    Pairs of `param_hash` or without hash, with both witnesses in `wids`, to be scored one by one whatever their rank:
    - REMAPPED pairs (force: only categorized ones, the new score files absorb or delete the others)
    - categorized pairs without score (MANUAL, PROPAGATED)
    - force: categorized pairs without hash (scored before hashes existed)
    """
    digits = Digitization.objects.filter(witness_id__in=wids).values("id")
    remapped, unscored = Q(similarity_type=SimilarityType.REMAPPED), Q(
        score__isnull=True
    )
    q = (
        ~UNCATEGORIZED & (remapped | unscored | Q(similarity_hash__isnull=True))
        if force
        else remapped | (~UNCATEGORIZED & unscored)
    )
    rows = RegionPair.objects.filter(
        q,
        Q(similarity_hash=param_hash) | Q(similarity_hash__isnull=True),
        digit_1__in=digits,
        digit_2__in=digits,
    )
    return [list(p) for p in rows.order_by().values_list("img_1", "img_2").distinct()]


DOC_REF_RE = re.compile(r"^\w+-\w+$")


def process_results(data, completed=True):
    """
    :param data: {
        "dataset_url": self.dataset.get_absolute_url(),
        "results_url": [{
            "doc_pair": doc_pair_ref,
            "result_url": result_url  => result_url returns a downloadable JSON
        }, {...}],
    }
    :param completed: whether the treatment is achieved or these are intermediary results

    result_url JSON file content
    {
        "parameters": {
            "algorithm": "cosine | segswap",
            "topk": "nb of kept best matches after cosine similarity",
            "feat_net": "backbone extractor",
            "segswap_prefilter": self.segswap_prefilter,
            "segswap_n": "nb of kept best matches after segswap similarity",
            "raw_transpositions": "list of transforms",
            "transpositions": "list of transforms",
        },
        "index": {
            "sources": {
                doc_ref: doc.to_dict()
                for doc in self.dataset.documents
            },
            "images": [{
                "uid": "wit<id>_<digit><id>_<page_nb>_<x,y,w,h>",
                "src": "iiif image url",
                "path": "path in API",
                "metadata": self.metadata,
                "doc_uid": doc_ref
            }, {...}],
            "transpositions": "list of transforms",
        },
        "pairs": [(im1_idx, im2_idx, score, tr1, tr2), (...)],
    }
    """
    from app.webapp.models.treatment import Treatment
    from app.similarity.tasks import download_similarity_file, rescore_similarity_pairs

    log(f"[process_results] Received data", msg_type="cyan")
    log(data, msg_type="cyan")

    output = (data or {}).get("output", {})
    if not output:
        log("No similarity results to download")
        return

    results_url = output.get("results_url", [])
    if not results_url:
        error = output.get("error") or ["No similarity results to process"]
        log(error)
        raise ValueError(error if isinstance(error, str) else "\n".join(error))
    # TODO when process results error => treatment status should be error

    treatment = Treatment.objects.get(id=data["experiment_id"])
    params = similarity_param(treatment.api_parameters)
    h = similarity_hash(params)
    for pair_scores in results_url:
        doc_pair, url = pair_scores.get("doc_pair"), pair_scores["result_url"]
        if doc_pair == "pairs":
            rescore_similarity_pairs.delay(url, h)
        elif DOC_REF_RE.match(doc_pair):
            # "dataset" scores (entire set of document pairs, used in AIKON-demo) are not indexed
            path = score_file(*doc_pair.split("-"), h)
            # with force, a file not written by this treatment is replaced (results are notified twice: PROGRESS and SUCCESS)
            replace = (
                params["force"]
                and path.exists()
                and path.stat().st_mtime < treatment.requested_on.timestamp()
            )
            if replace or not path.exists():
                download_similarity_file.delay(url, str(path), replace, params["force"])


def prepare_document(document: Witness | Digitization | RegionExtraction, **kwargs):
    source_type = kwargs.get("source_type", SourceType.REGIONS)

    # run similarity on document pages
    if source_type == SourceType.PAGES:
        digits = (
            document.get_digits() if hasattr(document, "get_digits") else [document]
        )
        return [
            {"type": "iiif", "src": d.get_manifest_url(), "uid": d.get_ref()}
            for d in digits
        ]

    documents = []
    for wid in get_witness_ids(document):
        if not any(
            has_annotation(d.get_ref())
            for d in Digitization.objects.filter(witness_id=wid)
        ):
            log(
                f"[prepare_document] Witness #{wid} skipped: no annotation in aiiinotate (or aiiinotate unreachable)",
                msg_type="warning",
            )
            continue
        documents.append(
            {
                "type": "url_list",
                "src": f"{APP_URL}/{APP_NAME}/witness/{wid}/list/",
                "uid": str(wid),
            }
        )
    return documents


def send_request(witnesses):
    """
    To relaunch similarity request in case the automatic process has failed
    """
    return tasking.task_request("similarity", witnesses)


def load_scores(score_path: Path):
    if not score_path.exists():
        return None

    ext = score_path.suffix
    if ext == ".json":
        return load_json_file(score_path)
    # Should not be used anymore: to delete
    if ext == ".npy":
        return load_npy_file(score_path)
    return None


def download_scores(url: str, path: Path, replace=False) -> bool:
    if path.exists() and not replace:
        return False
    response = requests.get(url, timeout=(10, 300))
    response.raise_for_status()
    orjson.loads(response.content)  # an invalid file would mark the pair as computed
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_bytes(response.content)
    tmp.replace(path)
    return True


def load_json_file(score_path):
    try:
        with open(score_path, "rb") as f:
            content = f.read()

        if not content:
            log(f"[load_json_file] Empty file: {score_path}")
            return None

        return json_to_scores_tuples(orjson.loads(content))
    except orjson.JSONDecodeError as e:
        log(f"[load_json_file] invalid JSON in {score_path}", e)
    except Exception as e:
        log(f"[load_json_file] Unexpected error in {score_path}", e)
    return None


def load_npy_file(score_path):
    try:
        return np.load(score_path, allow_pickle=True)
    except FileNotFoundError as e:
        log(f"[load_npy_file] no score file for {score_path}", e)
        return None


def json_to_scores_tuples(json_scores):
    """
    Convert JSON scores format to list of (score, img1, img2) tuples.

    Input JSON format:
    {
        "index": {
            "images": [{"id": "img_001_x,y,w,h", ...}, ...]
        },
        "pairs": [[idx1, idx2, score, rot1, rot2], ...]
    }

    Returns:
    List of tuples: [(score, img1, img2), ...]
    """
    if not json_scores or "index" not in json_scores or "pairs" not in json_scores:
        return []

    images = []
    for img in json_scores["index"].get("images", []):
        img_id = img.get("id", "")
        doc_uid = img.get("doc_uid", "")

        # Remove .jpg if present to normalize
        img_id = img_id.removesuffix(".jpg")

        if img_id.startswith("wit"):
            # Region format: id already contains full ref
            ref = f"{img_id}.jpg"
        else:
            # Page format: construct from doc_uid + page number
            ref = f"{doc_uid}_{img_id}.jpg"

        images.append(ref)

    return [
        (float(pair[2]), images[pair[0]], images[pair[1]])
        for pair in json_scores["pairs"]
    ]


def get_doc_refs_from_records(records, source_type=SourceType.REGIONS) -> list[str]:
    """Extract all document refs from records (Witness/Digitization/RegionExtraction)."""
    refs = []
    for record in records:
        if source_type == SourceType.PAGES:
            digits = record.get_digits() if hasattr(record, "get_digits") else [record]
            refs.extend(d.get_ref() for d in digits if digits)
        else:
            region_extractions = (
                record.get_region_extractions()
                if hasattr(record, "get_region_extractions")
                else [record]
            )
            refs.extend(
                region.get_ref() for region in region_extractions if region_extractions
            )
    return refs


def similarity_param(parameters: dict | None) -> dict:
    """Explicit parameters value casting"""
    p = SIM_DEFAULTS | {
        k: v for k, v in (parameters or {}).items() if v not in (None, "")
    }
    return p | {
        k: type(d)(p[k]) for k, d in SIM_DEFAULTS.items() if not isinstance(d, list)
    }


def similarity_hash(parameters: dict) -> str:
    """
    ⚠️ Must reproduce exactly the "parameters" returned by the API in score files,
    hashed in process_results(): any difference makes get_existing_pairs() ineffective
    """
    p = similarity_param(parameters)
    return SimilarityParameters.get_or_create_from_params(
        {
            "algorithm": p["algorithm"],
            "topk": p["cosine_n_filter"],
            "feat_net": p["feat_net"],
            "segswap_prefilter": p["segswap_prefilter"],
            "segswap_n": p["segswap_n"],
            "raw_transpositions": p["transpositions"],
        }
    )


def get_existing_pairs(doc_refs: set[str], parameters: dict) -> set[str]:
    """
    Document pairs already computed for these parameters
    - regions (doc_refs = witness ids): region pairs of the hash exist between the two witnesses,
      with or without score file (imported or restored pairs, hash set by hand)
    - pages (doc_refs = digitization refs): the score file exists
    ⚠️ regions added after the computation are not compared unless forced
    """
    param_hash = similarity_hash(parameters)
    if parameters["source_type"] == SourceType.REGIONS:
        wit = dict(
            Digitization.objects.filter(witness_id__in=doc_refs).values_list(
                "id", "witness_id"
            )
        )
        digit_pairs = (
            RegionPair.objects.filter(
                similarity_hash=param_hash,
                digit_1__in=list(wit),
                digit_2__in=list(wit),
                img_1__contains=",",  # region pairs only (page names have no bbox)
            )
            .values_list("digit_1", "digit_2")
            .distinct()
        )
        return {
            RegionPair.order_pair((str(wit[d1]), str(wit[d2])), as_string=True)
            for d1, d2 in digit_pairs
        }

    # TODO pages: rely on score files, page pairs could be checked in the same way (names without bbox)
    return {
        RegionPair.order_pair((r1, r2), as_string=True)
        for r1, r2 in combinations_with_replacement(sorted(doc_refs), 2)
        if score_file(r1, r2, param_hash).exists()
    }


def score_file(r1: str, r2: str, param_hash: str) -> Path:
    return (
        Path(SCORES_PATH)
        / RegionPair.order_pair((r1, r2), as_string=True)
        / f"{param_hash}.json"
    )


def score_file_to_db(file_path, clean=False):
    """
    Load scores from a .json file and add all of its pairs in the RegionPair table
    Rows of the same images without hash are absorbed (see absorb)
    If clean (forced recomputation), uncategorized pairs of the same hash absent from the file are deleted
    """
    p = Path(file_path)
    pair_scores = load_scores(p)
    pair_ref, param_hash = p.parent.name, p.stem
    if not pair_scores or not pair_ref:
        return False

    ref_1, ref_2 = RegionPair.order_pair(pair_ref)

    # Determine if this is region-based or page-based
    is_regions = "_anno" in ref_1

    if is_regions:
        rid1 = int(ref_1.split("_anno")[1])
        rid2 = int(ref_2.split("_anno")[1])
    else:
        rid1 = rid2 = None

    try:
        pairs = [
            new_pair(
                *RegionPair.order_pair((img1, img2), normalize=True),
                float(score),
                rid1,
                rid2,
            )
            for score, img1, img2 in pair_scores
            if float(score) > 0
        ]
    except ValueError as e:
        log(f"[score_file_to_db] error while processing {pair_ref}", e)
        return False

    try:
        with transaction.atomic():
            kept = absorb(pairs, param_hash)
            if clean and ref_1.isdigit() and ref_2.isdigit():
                delete_absent_pairs(ref_1, ref_2, param_hash, kept)
            # TODO pages: score files named after digitization refs are not cleaned
    except Exception as e:
        log(f"[score_file_to_db] error while adding pairs to db {pair_ref}", e)
        return False

    spread_categories(kept)

    log(f"Processed {len(pair_scores)} image pairs from {pair_ref}", msg_type="success")
    return True


UNCATEGORIZED = Q(category__isnull=True) & (
    Q(category_x__isnull=True) | Q(category_x=[])
)
ABSORBED_FIELDS = [
    "score",
    "similarity_type",
    "similarity_hash",
    "category",
    "category_x",
]


def uncategorized(qs: QuerySet) -> QuerySet:
    return qs.filter(UNCATEGORIZED)


def new_pair(
    img_1: str, img_2: str, score: float, rid_1=None, rid_2=None
) -> RegionPair:
    ref_1, ref_2 = parse_img(img_1), parse_img(img_2)
    return RegionPair(
        img_1=img_1,
        img_2=img_2,
        digit_1=ref_1.digit,
        digit_2=ref_2.digit,
        score=score,
        regions_id_1=rid_1,
        regions_id_2=rid_2,
        similarity_type=SimilarityType.AUTO,
    )


def absorb(
    pairs: list[RegionPair], param_hash: str, create=True
) -> set[tuple[str, str]]:
    """
    Write the scores of `pairs` under `param_hash`, one row per pair of images:
    rows of `param_hash` and without hash are merged (categories united, MANUAL kept, others become AUTO)
    A score <= 0 deletes uncategorized pairs and is set to 0 for categorized ones
    create: pairs without row are created (score files), otherwise ignored (pairs scored one by one)
    Returns the pairs of images as stored
    """
    scored = {(p.img_1, p.img_2): p for p in RegionPair.objects.orient(pairs)}
    to_create, to_update, to_delete = [], [], []
    with transaction.atomic():
        rows = defaultdict(list)
        for rp in (
            RegionPair.objects.select_for_update()
            .filter(
                Q(similarity_hash=param_hash) | Q(similarity_hash__isnull=True),
                img_1__in={a for a, _ in scored},
                img_2__in={b for _, b in scored},
            )
            .order_by("id")
        ):
            if (rp.img_1, rp.img_2) in scored:
                rows[rp.img_1, rp.img_2].append(rp)

        for key, new in scored.items():
            if not (group := rows.get(key) or ([new] if create else [])):
                continue
            keep = next((rp for rp in group if rp.similarity_hash), group[0])
            before = [getattr(keep, f) for f in ABSORBED_FIELDS]
            to_delete += [rp.id for rp in group if rp is not keep]
            keep.category = min(
                (rp.category for rp in group if rp.category is not None), default=None
            )
            keep.category_x = sorted({u for rp in group for u in rp.category_x or []})
            if new.score <= 0 and keep.category is None and not keep.category_x:
                to_delete += [keep.id] if keep.pk else []
                continue
            keep.score = max(new.score, 0.0)
            keep.similarity_hash = param_hash
            keep.similarity_type = (
                SimilarityType.MANUAL
                if any(rp.similarity_type == SimilarityType.MANUAL for rp in group)
                else SimilarityType.AUTO
            )
            if not keep.pk:
                to_create.append(keep)
            elif [getattr(keep, f) for f in ABSORBED_FIELDS] != before:
                to_update.append(keep)

        RegionPair.objects.filter(id__in=to_delete).delete()
        RegionPair.objects.bulk_update(to_update, ABSORBED_FIELDS, batch_size=1000)
        RegionPair.objects.bulk_create(
            to_create, batch_size=1000, ignore_conflicts=True
        )

    log(
        f"[absorb] {len(to_create)} pairs created, {len(to_update)} updated, {len(to_delete)} deleted",
        msg_type="success",
    )
    return set(scored)


def delete_absent_pairs(
    wid_1: str, wid_2: str, param_hash: str, kept: set[tuple[str, str]]
):
    """Delete the uncategorized AUTO, REMAPPED or PROPAGATED pairs of `param_hash` or without hash between two witnesses that their new score file does not contain"""
    d1, d2 = (
        Digitization.objects.filter(witness_id=wid).values("id")
        for wid in (wid_1, wid_2)
    )
    rows = uncategorized(
        RegionPair.objects.filter(
            Q(digit_1__in=d1, digit_2__in=d2) | Q(digit_1__in=d2, digit_2__in=d1),
            Q(similarity_hash=param_hash) | Q(similarity_hash__isnull=True),
            similarity_type__in=[
                SimilarityType.AUTO,
                SimilarityType.REMAPPED,
                SimilarityType.PROPAGATED,
            ],
        )
    ).values_list("id", "img_1", "img_2")
    if absent := [i for i, img_1, img_2 in rows if (img_1, img_2) not in kept]:
        RegionPair.objects.filter(id__in=absent).delete()
        log(f"[delete_absent_pairs] {len(absent)} pairs deleted for {wid_1}-{wid_2}")


def rescore_to_db(pair_scores: list[tuple[float, str, str]], param_hash: str):
    """Pairs scored one by one (names as stored, see pairs_to_score), absorbed by `param_hash`"""
    spread_categories(
        absorb(
            [new_pair(a, b, float(score)) for score, a, b in pair_scores],
            param_hash,
            create=False,
        )
    )


def spread_categories(pairs: set[tuple[str, str]]):
    """
    Apply the categories of the digitizations of `pairs` to their rows of every hash
    Called once the scores are committed: a failure is only logged
    """
    if not pairs:
        return
    try:
        inherit_categories(
            sorted({parse_img(img).digit for pair in pairs for img in pair}),
            dry_run=False,
            log=log,
        )
    except Exception as e:
        log("[spread_categories] failed to apply categories across hashes", e)


def get_digit_pairs(digit_id: int):
    return RegionPair.objects.filter(
        Q(digit_1=digit_id) | Q(digit_2=digit_id)
    ).values_list("digit_1", "digit_2", "img_1", "img_2")


def get_matched_regions(q_img: str, s_digit_id: int):
    return pairs_with(q_img, [s_digit_id])


def get_pairs_with_img(q_img: str):
    return list(RegionPair.objects.filter(Q(img_1=q_img) | Q(img_2=q_img)))


PAIR_FIELDS = (
    "img_1",
    "img_2",
    "digit_1",
    "digit_2",
    "score",
    "category",
    "category_x",
    "similarity_type",
    "similarity_hash",
)


def get_region_pairs_with(q_img, query_digit_ids, target_digit_ids=None):
    # query_digit_ids is implied by q_img: the digitization is encoded in the image name
    return list(
        pairs_with(q_img, target_digit_ids).values_list(*PAIR_FIELDS, named=True)
    )


def pair_tuple(row, q_img):
    is_q1 = row.img_1 == q_img
    return RegionPairTuple(
        score=row.score,
        q_img=q_img,
        s_img=row.img_2 if is_q1 else row.img_1,
        q_digit=row.digit_1 if is_q1 else row.digit_2,
        s_digit=row.digit_2 if is_q1 else row.digit_1,
        category=row.category,
        category_x=row.category_x or [],
        similarity_type=row.similarity_type,
        similarity_hash=row.similarity_hash,
    )


def pairs_with(q_img: str, digit_ids=None) -> QuerySet:
    if digit_ids is None:
        return RegionPair.objects.filter(Q(img_1=q_img) | Q(img_2=q_img))
    return RegionPair.objects.filter(
        Q(img_1=q_img, digit_2__in=digit_ids) | Q(img_2=q_img, digit_1__in=digit_ids)
    )


def pair_priority(pair: RegionPairTuple, user_id) -> tuple:
    is_x = user_id in pair.category_x
    if pair.category is None:
        # uncategorized get 3.5 as rank so they rank in between cat 3 and cat 4
        return (0 if is_x else 3.5), 0, -(pair.score or 0)

    return (
        pair.category,
        0 if is_x else 1 if pair.similarity_type == SimilarityType.MANUAL else 2,
        -(pair.score or 0),
    )


def is_auto(pair: RegionPairTuple, user_id) -> bool:
    return (
        pair.category is None
        and user_id not in pair.category_x
        and pair.similarity_type in (SimilarityType.AUTO, SimilarityType.REMAPPED)
    )


def get_best_pairs(
    q_img, rows, excluded_categories=(), topk=None, user_id=None, export=False
):
    pairs = sorted(
        (RegionPairTuple.of(r, q_img) for r in rows),
        key=lambda p: pair_priority(p, user_id),
    )
    if export:
        return pairs

    seen, result, n_auto = set(), [], 0
    for p in pairs:
        if p.s_img in seen:
            continue

        seen.add(p.s_img)
        if p.category in excluded_categories:
            continue

        if topk and is_auto(p, user_id):
            n_auto += 1
            if n_auto > topk:
                continue

        result.append(p)
    return result


def delete_pairs_with_digit(digit_id: int):
    RegionPair.objects.filter(Q(digit_1=digit_id) | Q(digit_2=digit_id)).delete()


def get_digit_imgs(digit_id: int) -> list[str]:
    imgs_1 = RegionPair.objects.filter(digit_1=digit_id).values_list("img_1", flat=True)
    imgs_2 = RegionPair.objects.filter(digit_2=digit_id).values_list("img_2", flat=True)
    return list(set(imgs_1) | set(imgs_2))


def validate_img_ref(img_string):
    # wit<id>_<digit><id>_<canvas_nb>_<x>,<y>,<h>,<w>
    pattern = r"^wit\d+_[a-zA-Z]{3}\d+_\d+_\d+,\d+,\d+,\d+$"
    return bool(re.match(pattern, img_string))


def doc_pairs(doc_ids: list):
    if isinstance(doc_ids, list) and len(doc_ids) > 0:
        return list(combinations_with_replacement(doc_ids, 2))
    raise ValueError("Input must be a non-empty list of ids.")


def check_computed_pairs(regions_refs):
    regions_to_send = []
    for ref1, ref2 in doc_pairs(regions_refs):
        wid1, wid2 = (str(parse_ref(ref)["wit"][1]) for ref in (ref1, ref2))
        # score folders are named "regions_ref1-regions_ref2" (legacy) or "wid1-wid2"
        # a pair counts as computed whatever its parameters hash → only relaunches pairs never computed
        if not any(
            any(
                (Path(SCORES_PATH) / RegionPair.order_pair(pair, as_string=True)).glob(
                    "*.json"
                )
            )
            for pair in [(ref1, ref2), (wid1, wid2)]
        ):
            regions_to_send.extend((ref1, ref2))
    # return list of unique regions_ref involved in one of the pairs that are not already computed
    return list(set(regions_to_send))


def get_computed_pairs(regions_ref):
    """Score files of the pairs involving regions_ref or its witness"""
    refs = {regions_ref, str(parse_ref(regions_ref)["wit"][1])}
    return [
        str(score_file)
        for score_file in Path(SCORES_PATH).glob("*/*.json")
        if refs & set(score_file.parent.name.split("-"))
    ]


def get_all_pairs():
    return [str(score_file) for score_file in Path(SCORES_PATH).glob("*/*.json")]


def reset(match, api_refs, digit, tag: str) -> bool:
    for name in os.listdir(SCORES_PATH):
        if any(match(ref) for ref in name.split("-")) and not delete_path(
            Path(SCORES_PATH) / name
        ):
            log(f"[{tag}] Failed to delete file {name}")

    for ref in api_refs:
        try:
            delete_api_similarity.delay(ref, algorithm=None, feat_net=None)
        except Exception as e:
            log(f"[{tag}] Error deleting API similarity for {ref}", e)

    try:
        delete_pairs_with_digit(digit.id)
    except Exception as e:
        log(f"[{tag}] Error deleting pairs for digit {digit}", e)
        return False
    return True


def reset_digit_similarity(digit) -> bool:
    """Delete all similarity data (score files, API data, RegionPairs) for a digitization"""
    digit_ref, wid = digit.get_ref(), str(digit.witness_id)
    return reset(
        # "regions_ref1-regions_ref2" (legacy) or "wid1-wid2" score folders
        lambda ref: ref in (wid, digit_ref) or ref.startswith(f"{digit_ref}_"),
        [*(regions.get_ref() for regions in digit.region_extractions.all()), wid],
        digit,
        "reset_digit_similarity",
    )


def reset_similarity(region_extraction: RegionExtraction) -> bool:
    try:
        regions_ref = region_extraction.get_ref()
        wid = str(get_witness_ids(region_extraction)[0])
    except Exception as e:
        log(
            f"[reset_similarity] Failed to retrieve refs for region extraction #{region_extraction.id}",
            e,
        )
        return False
    # TODO retrieve info on the algorithm and feature network used (in json score files)
    return reset(
        # "regions_ref1-regions_ref2" (legacy) or "wid1-wid2" score folders
        lambda ref: ref in (regions_ref, wid),
        [regions_ref, wid],
        region_extraction.get_digit(),
        "reset_similarity",
    )


def update_category_x(region_pair: RegionPair, user_id: int):
    """
    update the `category_x` field from a `region_pair`.
    category_x is a List[int] containing the user IDs of all users that have done a user_match on a category.
    """
    if region_pair.category_x is None:
        region_pair.category_x = []

    if user_id not in region_pair.category_x:
        region_pair.category_x.append(user_id)
    region_pair.category_x = [u for u in region_pair.category_x if u is not None]

    return region_pair


CATEGORY = Coalesce("category", Value(0))
TYPE_RANK = Case(
    *(When(similarity_type=t, then=Value(p)) for t, p in TYPE_PRIORITY.items()),
    default=Value(99),
)


def filter_pairs(
    digit_ids,
    exclusive=True,
    min_score=None,
    max_score=None,
    topk=None,
    exclude_self=False,
    categories=None,
    user_id=None,
    unique=False,
) -> QuerySet:
    """unique: one row per pair of images whatever its hash (all its rows share the same categories)"""
    if exclusive:
        query = Q(digit_1__in=digit_ids) & Q(digit_2__in=digit_ids)
    else:
        query = Q(digit_1__in=digit_ids) | Q(digit_2__in=digit_ids)

    if min_score is not None:
        query &= Q(score__gte=min_score)

    if max_score is not None:
        query &= Q(score__lte=max_score)

    if exclude_self:
        query &= ~Q(digit_1=F("digit_2"))

    qs = RegionPair.objects.filter(query)
    if categories:
        cat_query = Q(cat__in=categories)
        if user_id and SimilarityCategory.USER_MATCH in categories:
            cat_query |= Q(category_x__contains=[user_id])
        qs = qs.alias(cat=CATEGORY).filter(cat_query)

    if unique:
        qs = RegionPair.objects.filter(
            id__in=qs.order_by(
                "img_1", "img_2", TYPE_RANK, F("score").desc(nulls_last=True)
            )
            .distinct("img_1", "img_2")
            .values("id")
        )

    qs = qs.order_by(F("score").desc(nulls_first=True))
    return qs[:topk] if topk else qs


def normalize_pair(img_1: str, img_2: str):
    return RegionPair.order_pair((img_1, img_2), normalize=True)


def stream_pairs_ndjson(qs: QuerySet, user_id: int | None, batch_size=10_000):
    """Gzipped NDJSON, one line per batch: [new image names, flat (img_idx_1, img_idx_2, score, category, is_user_match, similarity_type) tuples]"""
    with transaction.atomic(), closing(
        qs.values_list(
            "img_1", "img_2", "score", CATEGORY, "category_x", "similarity_type"
        ).iterator(chunk_size=batch_size)
    ) as rows:
        ids, gz = {}, zlib.compressobj(1, wbits=31)
        while batch := list(islice(rows, batch_size)):
            n = len(ids)
            flat = [
                v
                for a, b, s, c, x, t in batch
                for v in (
                    ids.setdefault(a, len(ids)),
                    ids.setdefault(b, len(ids)),
                    s and round(s, 4),
                    c,
                    int(user_id in (x or ())),
                    t,
                )
            ]
            new = [*islice(reversed(ids), len(ids) - n)][::-1]
            yield gz.compress(orjson.dumps([new, flat]) + b"\n") + gz.flush(
                zlib.Z_SYNC_FLUSH
            )
        yield gz.flush()


def export_pairs(digit_ids, after_id: int = 0, limit: int | None = None) -> dict:
    """
    Export RegionPair rows where BOTH digitizations are in `digit_ids`
    (self-contained: every reference resolves on re-import).
    Cursor-paginated on pk. limit=None returns all rows.
    """
    if not digit_ids:
        return {"pairs": [], "next_cursor": None, "count": 0}

    qs = RegionPair.objects.filter(
        digit_1__in=digit_ids, digit_2__in=digit_ids, id__gt=after_id
    ).order_by("id")

    rows = list(qs if limit is None else qs[: limit + 1])
    has_more = limit is not None and len(rows) > limit
    if has_more:
        rows = rows[:limit]

    return {
        "pairs": [p.to_dict() for p in rows],
        "next_cursor": rows[-1].id if has_more else None,
        "count": len(rows),
    }


def in_pairs(*imgs: str) -> bool:
    return RegionPair.objects.filter(Q(img_1__in=imgs) | Q(img_2__in=imgs)).exists()


def stored_name(img: str, ref: ImgRef) -> str | None:
    """Name of this box in RegionPair, tolerating rounding differences between sources"""
    if in_pairs(img):
        return img
    box = parse_bbox(ref.bbox)
    return next(
        (
            s
            for s in sorted(fetch_distinct_images([ref.digit]))
            if (r := parse_img(s, True))
            and r.bbox
            and int(r.page) == int(ref.page)
            and close(parse_bbox(r.bbox), box)
        ),
        None,
    )


def load_regions(
    data: dict, *keys: str, paired: tuple[str, ...]
) -> tuple[list[str], list[ImgRef]]:
    imgs = [add_jpg(data[k]) for k in keys]
    refs = [parse_img(i, True) for i in imgs]
    if not all(r and r.bbox for r in refs):
        raise ValueError(f"Invalid region: {' / '.join(imgs)}")

    if refs[0].digit != refs[1].digit:
        raise ValueError("Duplicates must belong to the same digitization")

    stored = {k: stored_name(i, r) for k, i, r in zip(keys, imgs, refs)}
    if not any(stored[k] for k in paired):
        raise ValueError(
            f"No pair contains {' or '.join(add_jpg(data[k]) for k in paired)}"
        )

    imgs = [stored[k] or i for k, i in zip(keys, imgs)]
    if imgs[0] == imgs[1]:
        raise ValueError("The two regions must differ")

    return imgs, [parse_img(i) for i in imgs]


def find_annotations(refs: list[ImgRef]) -> list[dict | None] | None:
    """get aiiinotations associated with the image reference"""
    annos = {
        c: get_canvas_annotations(*c) for c in {(r.digit, int(r.page)) for r in refs}
    }
    if None in annos.values():
        return None
    return [
        next(
            (
                a
                for a in annos[r.digit, int(r.page)]
                if close(
                    parse_bbox(get_coord_from_annotation(a, as_str=True)),
                    parse_bbox(r.bbox),
                )
            ),
            None,
        )
        for r in refs
    ]


def categorize_pairs(
    categories: dict, similarity_type=SimilarityType.PROPAGATED
) -> dict:
    """
    categories: {(img_1, img_2): category}
    Override the category and create missing pairs
    """
    pairs = {
        (p.img_1, p.img_2): p
        for p in RegionPair.objects.orient(
            [
                RegionPair.build(
                    img_1,
                    img_2,
                    category=category,
                    similarity_type=similarity_type,
                    score=None,
                    category_x=[],
                )
                for (img_1, img_2), category in categories.items()
            ]
        )
    }
    if not pairs:
        return {"created": 0, "updated": 0}

    q, by_category = Q(), defaultdict(Q)
    for (img_1, img_2), p in pairs.items():
        q |= Q(img_1=img_1, img_2=img_2)
        by_category[p.category] |= Q(img_1=img_1, img_2=img_2)

    existing = set(RegionPair.objects.filter(q).values_list("img_1", "img_2"))
    to_create = [p for key, p in pairs.items() if key not in existing]
    RegionPair.objects.bulk_create(to_create)

    return {
        "created": len(to_create),
        "updated": sum(
            RegionPair.objects.filter(cq).exclude(category=c).update(category=c)
            for c, cq in by_category.items()
        ),
    }


def import_pairs(pairs: list[dict]) -> dict:
    """
    pair format [{"img_1", "img_2", ?"score", ?"category", ?"similarity_hash"}]
    - score: updated as from an API score file
    - category: overrides the category of existing pairs
    - type: new pairs are set as MANUAL
    """
    import_hash = SimilarityParameters.get_or_create_from_params(
        {"algorithm": "import"}
    )
    scored, categories = defaultdict(list), {}
    for p in pairs:
        if (score := safe_float(p.get("score"))) is not None:
            scored[p.get("similarity_hash") or import_hash].append(
                RegionPair.build(p["img_1"], p["img_2"], score=score)
            )
        if p.get("category") is not None:
            categories[p["img_1"], p["img_2"]] = SimilarityCategory(
                int(p["category"])
            ).value

    with transaction.atomic():
        kept = set().union(*(absorb(pairs, h) for h, pairs in scored.items()))
        results = categorize_pairs(categories, SimilarityType.MANUAL)

    spread_categories(kept)
    return {"scored": len(kept), **results}
