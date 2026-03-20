import json
import os
import re
from enum import IntEnum

import numpy as np
from typing import Set, List

import orjson
import requests
from itertools import combinations_with_replacement

from pathlib import Path
from django.db import transaction, connection
from django.db.models import Q, F

from app.similarity.const import SCORES_PATH
from app.config.settings import APP_URL, APP_NAME
from app.similarity.models.region_pair import (
    RegionPair,
    RegionPairTuple,
    parse_img,
    add_jpg,
)
from app.similarity.models.similarity_parameters import (
    SimilarityParameters,
    generate_hash,
)
from app.similarity.tasks import delete_api_similarity
from app.webapp.models.digitization import Digitization
from app.webapp.models.regions import Regions
from app.webapp.models.witness import Witness
from app.webapp.utils import tasking
from app.webapp.utils.functions import delete_path
from app.webapp.utils.logger import log
from config.settings import APP_LANG


class SimilarityType(IntEnum):
    AUTO = 1
    MANUAL = 2
    PROPAGATED = 3


class SimilarityCategory(IntEnum):
    EXACT_MATCH = 1
    PARTIAL_MATCH = 2
    SEMANTIC_MATCH = 3
    NO_MATCH = 4
    USER_MATCH = 5


class SourceType:
    REGIONS = "regions"
    PAGES = "pages"


################################################################
# ⚠️   prepare_request() & process_results() are mandatory  ⚠️ #
# ⚠️ function used by Treatment to generate request payload ⚠️ #
# ⚠️    and save results files when sends back by the API   ⚠️ #
################################################################


def prepare_request(witnesses, treatment_id, parameters=None):
    """Prepare similarity request, excluding already computed pairs."""
    source_type = (parameters or {}).get("source_type", SourceType.REGIONS)
    doc_refs = get_doc_refs_from_records(witnesses, source_type)

    if not doc_refs:
        raise ValueError(
            "No documents with extracted regions for similarity computation"
            if source_type == SourceType.REGIONS
            else "No digitizations for similarity computation"
        )

    skip_pairs = []
    if parameters:
        all_pairs = {
            RegionPair.order_pair((r1, r2), as_string=True)
            for r1, r2 in combinations_with_replacement(set(doc_refs), 2)
        }
        existing = get_existing_pairs(doc_refs, parameters)
        if existing and existing == all_pairs:
            return {
                "message": "All similarity pairs already computed for these parameters"
            }
        skip_pairs = list(existing)

    return tasking.prepare_request(
        witnesses,
        treatment_id,
        prepare_document,
        "similarity",
        {**(parameters or {}), "skip_pairs": skip_pairs},
    )


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
    from app.similarity.tasks import process_similarity_file

    log(f"[process_results] Received data", msg_type="cyan")
    log(data, msg_type="cyan")

    output = data.get("output", {})
    if not data or not output:
        log("No similarity results to download")
        return

    results_url = output.get("results_url", [])
    if not results_url:
        error = output.get("error", ["No similarity results to process"])
        log(error)
        raise ValueError("\n".join(error))
    # TODO when process results error => treatment status should be error

    for pair_scores in results_url:
        regions_ref_pair = pair_scores.get("doc_pair")
        score_url = pair_scores.get("result_url")

        if regions_ref_pair == "dataset":
            # do not index scores for the entire set of document pairs (used in AIKON-demo)
            continue
        regions_ref_pair = RegionPair.order_pair(regions_ref_pair, as_string=True)

        try:
            response = requests.get(score_url, stream=True)
            response.raise_for_status()
            json_content = response.json()

            params = json_content.get("parameters", {})
            param_hash = SimilarityParameters.get_or_create_from_params(params)

            score_file = Path(f"{SCORES_PATH}/{regions_ref_pair}/{param_hash}.json")
            os.makedirs(f"{SCORES_PATH}/{regions_ref_pair}", exist_ok=True)
            if score_file.exists():
                # This should be avoided by get_existing_pairs > skip_pairs in prepare_request
                log(
                    f"[process_results] File {score_file} already exists, skipping download"
                )
                continue

            with open(score_file, "wb") as f:
                json_content["result_url"] = score_url
                f.write(orjson.dumps(json_content))

        except Exception as e:
            log(
                f"[process_results] Could not download similarity scores from {score_url}",
                e,
            )
            continue

        try:
            # process_similarity_file task calls score_file_to_db()
            process_similarity_file.delay(str(score_file))
        except Exception as e:
            log(
                f"[process_results] Could not process similarity scores from {score_url}",
                e,
            )
            raise e
    return


def prepare_document(document: Witness | Digitization | Regions, **kwargs):
    source_type = kwargs.get("source_type", SourceType.REGIONS)

    if source_type == SourceType.PAGES:
        digits = (
            document.get_digits() if hasattr(document, "get_digits") else [document]
        )
        if not digits:
            raise ValueError(
                f"'{document}' has no digitizations"
                if APP_LANG == "en"
                else f"« {document} » n'a pas de numérisations"
            )
        return [
            {"type": "iiif", "src": d.get_manifest_url(), "uid": d.get_ref()}
            for d in digits
        ]

    regions = document.get_regions() if hasattr(document, "get_regions") else [document]
    if not regions:
        raise ValueError(
            f"'{document}' has no extracted regions for similarity computation"
            if APP_LANG == "en"
            else f"« {document} » n'a pas de régions extraites pour le calcul de similarité"
        )
    return [
        {"type": "url_list", "src": f"{APP_URL}/{APP_NAME}/{ref}/list", "uid": ref}
        for ref in [r.get_ref() for r in regions]
    ]


def send_request(witnesses):
    """
    To relaunch similarity request in case the automatic process has failed
    """
    tasking.task_request("similarity", witnesses)


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
    """Extract document refs from records based on source type."""
    refs = []
    for record in records:
        if source_type == SourceType.PAGES:
            digits = record.get_digits() if hasattr(record, "get_digits") else [record]
            refs.extend(d.get_ref() for d in digits if digits)
        else:
            regions = (
                record.get_regions() if hasattr(record, "get_regions") else [record]
            )
            refs.extend(r.get_ref() for r in regions if regions)
    return refs


def get_existing_pairs(doc_refs: list[str], parameters: dict) -> set[str]:
    """
    Check which document pairs already have similarity results for given parameters.
    Returns set of pair identifiers like "ref1-ref2" (sorted alphabetically).
    """
    # Reproduce API format to generate hash
    params = {
        "algorithm": str(parameters.get("algorithm", "cosine")),
        "topk": int(parameters.get("cosine_n_filter", 20)),
        "feat_net": str(parameters.get("feat_net", "dino_deitsmall16_pretrain")),
        "segswap_prefilter": bool(parameters.get("segswap_prefilter", True)),
        "segswap_n": int(parameters.get("segswap_n", 10)),
        "raw_transpositions": ["none"],
    }

    param_hash = generate_hash(params)
    log(f"[get_existing_pairs] Checking existing pairs for hash {param_hash}")

    existing = set()
    for ref1, ref2 in combinations_with_replacement(sorted(set(doc_refs)), 2):
        for pair_ref in [f"{ref1}-{ref2}", f"{ref2}-{ref1}"]:
            if (Path(SCORES_PATH) / pair_ref / f"{param_hash}.json").exists():
                existing.add(pair_ref)

    return existing


def score_file_to_db(file_path):
    """
    Load scores from a .json file and add all of its pairs in the RegionPair table
    If pair already exists, only score is updated
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

    pairs_to_update = []
    try:
        for score, img1, img2 in pair_scores:
            score = float(score)
            if score <= 0:
                continue

            img1, img2 = RegionPair.order_pair((img1, img2))
            ref1, ref2 = parse_img(img1), parse_img(img2)
            pairs_to_update.append(
                RegionPair(
                    img_1=img1,
                    img_2=img2,
                    digit_1=ref1.digit,
                    digit_2=ref2.digit,
                    score=score,
                    regions_id_1=rid1,
                    regions_id_2=rid2,
                    similarity_type=SimilarityType.AUTO,
                    similarity_hash=param_hash,
                )
            )
    except ValueError as e:
        log(f"[score_file_to_db] error while processing {pair_ref}", e)
        return False

    # Bulk update existing pairs
    try:
        with transaction.atomic():
            RegionPair.objects.bulk_update_or_create(
                pairs_to_update,
                update_fields=[
                    "score",
                    "digit_1",
                    "digit_2",
                    "regions_id_1",
                    "regions_id_2",
                    "similarity_type",
                ],
                match_fields=["img_1", "img_2", "similarity_hash"],
            )
    except Exception as e:
        log(f"[score_file_to_db] error while adding pairs to db {pair_ref}", e)
        return False

    log(f"Processed {len(pair_scores)} image pairs from {pair_ref}", msg_type="success")
    return True


def get_compared_digit_ids(digit_id):
    pairs = RegionPair.objects.filter(
        Q(digit_1=digit_id) | Q(digit_2=digit_id)
    ).values_list("digit_1", "digit_2")

    return list({int(d2) if int(d1) == digit_id else int(d1) for d1, d2 in pairs})


def get_digit_pairs(digit_id: int):
    return RegionPair.objects.filter(
        Q(digit_1=digit_id) | Q(digit_2=digit_id)
    ).values_list("digit_1", "digit_2", "img_1", "img_2")


def get_matched_regions(q_img: str, s_digit_id: int):
    return RegionPair.objects.filter(
        (Q(img_1=q_img) & Q(digit_2=s_digit_id))
        | (Q(img_2=q_img) & Q(digit_1=s_digit_id))
    )


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
    if target_digit_ids is None:
        qs = RegionPair.objects.filter(Q(img_1=q_img) | Q(img_2=q_img))
        return list(qs.values_list(*PAIR_FIELDS, named=True))
    query = (
        Q(img_1=q_img)
        & Q(digit_1__in=query_digit_ids)
        & Q(digit_2__in=target_digit_ids)
    ) | (
        Q(img_2=q_img)
        & Q(digit_2__in=query_digit_ids)
        & Q(digit_1__in=target_digit_ids)
    )
    if not bool(set(query_digit_ids) & set(target_digit_ids)):
        query &= ~Q(digit_1=F("digit_2"))
    qs = RegionPair.objects.filter(query)

    return list(qs.values_list(*PAIR_FIELDS, named=True))


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


def pair_priority(pair, user_id):
    is_manual = pair.similarity_type == SimilarityType.MANUAL or (
        pair.category_x and user_id in pair.category_x
    )
    is_propagated = pair.similarity_type == SimilarityType.PROPAGATED
    is_nomatch = pair.category == SimilarityCategory.NO_MATCH
    is_categorized = pair.category is not None and not is_nomatch

    # high priority => low priority
    if is_manual:
        group = 0
    elif is_propagated:
        group = 1
    elif is_categorized:
        group = 2
    elif pair.score is not None:
        group = 3
    elif is_nomatch:
        group = 4
    else:
        group = 5

    sub = pair.category if is_categorized else 0
    return group, sub, -(pair.score or 0)


def get_best_pairs(
    q_img, region_pairs, excluded_categories, topk=None, user_id=None, export=False
):
    pairs = [pair_tuple(row, q_img) for row in region_pairs]
    pairs.sort(key=lambda p: pair_priority(p, user_id))

    if export:
        return pairs

    seen = set()
    result = []
    auto_count = 0

    for p in pairs:
        if p.s_img in seen:
            continue
        seen.add(p.s_img)

        if p.category in excluded_categories:
            continue

        is_manual = p.similarity_type == SimilarityType.MANUAL or (
            p.category_x and user_id in p.category_x
        )
        is_auto = (
            not is_manual
            and p.similarity_type != SimilarityType.PROPAGATED
            and p.category is None
            and p.score is not None
        )

        if is_auto and topk:
            auto_count += 1
            if auto_count > topk:
                continue

        result.append(p)

    return result


def delete_pairs_with_digit(digit_id: int):
    RegionPair.objects.filter(Q(digit_1=digit_id) | Q(digit_2=digit_id)).delete()


def get_digit_imgs(digit_id: int) -> list[str]:
    imgs_1 = RegionPair.objects.filter(digit_1=digit_id).values_list("img_1", flat=True)
    imgs_2 = RegionPair.objects.filter(digit_2=digit_id).values_list("img_2", flat=True)
    return list(set(imgs_1) | set(imgs_2))


# def get_best_pairs(
#     q_img: str,
#     region_pairs: List[RegionPair],
#     excluded_categories: Set[int],
#     topk: int | None = None,
#     user_id: int | None = None,
#     export: bool = False,
# ) -> List[Set[RegionPairTuple]]:
#     """
#     Process RegionPair objects and return a list.
#
#     :param q_img: Query image name
#     :param region_pairs: List of RegionPair objects
#     :param excluded_categories: List of category numbers to exclude
#     :param topk: Number of top scoring pairs to include (None = all)
#     :param user_id: int ID of the user asking for similarities
#     :param export: boolean value - when building pair for export, no sorting & no threshold
#     :return: List with structured data
#     """
#     manual_pairs = []
#     propagated_pairs = []  # propagated pairs that have been saved to database
#     categorized_pairs = []  # where category is not null
#     auto_pairs = []
#     auto_pairs_no_score = []
#     nomatch_pairs = []  # category == 4
#     added_images = set()
#     export_pairs = []  # pairs for export: all in big a single big list
#     export_pairs_no_score = []  # pairs for export without a score
#
#     for pair in region_pairs:
#         # (score, q_img, s_img, q_digit, s_digit, category, category_x, similarity_type, similarity_hash)
#         pair_data = pair.get_info(q_img)
#         if pair_data[2] in added_images:
#             # NOTE: first duplicate wins. Higher-priority pairs (e.g., manual) appearing later
#             #    will be discarded if lower-priority pairs (e.g., auto) were seen first.
#             continue
#         added_images.add(pair_data[2])
#
#         if export:
#             if pair.score is not None:
#                 export_pairs.append(pair_data)
#             else:
#                 export_pairs_no_score.append(pair_data)
#             continue
#
#         if pair.category in excluded_categories:
#             continue
#
#         if pair.similarity_type == SimilarityType.MANUAL or (
#             pair.category_x and user_id in pair.category_x
#         ):
#             manual_pairs.append(pair_data)
#         elif pair.similarity_type == SimilarityType.PROPAGATED:
#             propagated_pairs.append(pair_data)
#         elif pair.category == SimilarityCategory.NO_MATCH:
#             nomatch_pairs.append(pair_data)
#         elif pair.category is not None:
#             categorized_pairs.append(pair_data)
#         elif pair.score is not None:
#             auto_pairs.append(pair_data)
#         else:
#             auto_pairs_no_score.append(pair_data)
#
#     if export:
#         # sort by score, descending, finish with pairs with no score.
#         return (
#             sorted(export_pairs, key=lambda x: x[0], reverse=True)
#             + export_pairs_no_score
#         )
#
#     categorized_pairs.sort(key=lambda x: x[5])  # sort by category number, ascending
#
#     # sort by score, descending, finish with pairs with no score.
#     auto_pairs = (
#         sorted(auto_pairs, key=lambda x: x[0], reverse=True) + auto_pairs_no_score
#     )
#
#     if topk:
#         auto_pairs = auto_pairs[:topk]
#
#     return (
#         manual_pairs
#         + propagated_pairs
#         + categorized_pairs
#         + auto_pairs
#         + nomatch_pairs  # limit number of nomatch pairs?
#     )


def validate_img_ref(img_string):
    # wit<id>_<digit><id>_<canvas_nb>_<x>,<y>,<h>,<w>
    pattern = r"^wit\d+_[a-zA-Z]{3}\d+_\d+_\d+,\d+,\d+,\d+$"
    return bool(re.match(pattern, img_string))


def doc_pairs(doc_ids: list):
    if isinstance(doc_ids, list) and len(doc_ids) > 0:
        return list(combinations_with_replacement(doc_ids, 2))
    raise ValueError("Input must be a non-empty list of ids.")


def check_computed_pairs(regions_refs):
    # TODO incorrect with score files in json format located in different subfolders
    # TODO change that
    sim_files = os.listdir(SCORES_PATH)
    regions_to_send = []
    for pair in doc_pairs(regions_refs):
        if f"{RegionPair.order_pair(pair, as_string=True)}.npy" not in sim_files:
            regions_to_send.extend(pair)
    # return list of unique regions_ref involved in one of the pairs that are not already computed
    return list(set(regions_to_send))


def get_computed_pairs(regions_ref):
    # TODO incorrect with score files in json format located in different subfolders
    # TODO change that
    return [
        pair_file.replace(".npy", "")
        for pair_file in os.listdir(SCORES_PATH)
        if regions_ref in pair_file
    ]


def get_all_pairs():
    # TODO incorrect with score files in json format located in different subfolders
    # TODO change that
    return [pair_file.replace(".npy", "") for pair_file in os.listdir(SCORES_PATH)]


def reset_similarity(regions: Regions):
    regions_id = regions.id
    try:
        regions_ref = regions.get_ref()
    except Exception as e:
        log(f"[reset_similarity] Failed to retrieve region ref for id {regions_id}", e)
        return False
    for file in os.listdir(SCORES_PATH):
        if regions_ref in file:
            file_path = Path(SCORES_PATH) / file
            success = delete_path(file_path)
            if not success:
                log(f"[reset_similarity] Failed to delete file {file_path}")

    # TODO retrieve info on the algorithm and feature network used (in json score files)
    delete_api_similarity.delay(regions.get_ref(), algorithm=None, feat_net=None)

    try:
        delete_pairs_with_digit(regions.digitization_id)
    except Exception as e:
        log(f"[reset_similarity] Error deleting pairs with region id {regions_id}", e)

    return True


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


def filter_pairs(
    digit_ids, exclusive, min_score, max_score, topk, exclude_self, categories
):
    if exclusive:
        query = Q(digit_1__in=digit_ids) & Q(digit_2__in=digit_ids)
    else:
        query = Q(digit_1__in=digit_ids) | Q(digit_2__in=digit_ids)

    if min_score is not None:
        query &= Q(score__gte=float(min_score))

    if max_score is not None:
        query &= Q(score__lte=float(max_score))

    if exclude_self:
        query &= ~Q(digit_1=F("digit_2"))

    if categories:
        has_no_category = 0 in categories
        real_categories = [c for c in categories if c != 0]

        if has_no_category and real_categories:
            query &= Q(category__in=real_categories) | Q(category__isnull=True)
        elif has_no_category:
            query &= Q(category__isnull=True)
        elif real_categories:
            query &= Q(category__in=real_categories)

    pairs = RegionPair.objects.filter(query).order_by(F("score").desc(nulls_first=True))
    if not pairs.exists():
        log(f"[filter_pairs] No pairs found matching the criteria {query}")
        return []

    if topk is not None:
        topk = int(topk)
        pairs = pairs[:topk]

    return [p.to_dict() for p in pairs]


def retrieve_pair(img1, img2, create=False):
    img1, img2 = add_jpg(img1), add_jpg(img2)
    if img2 < img1:
        img1, img2 = img2, img1

    try:
        return RegionPair.objects.get(img_1=img1, img_2=img2), "OK"
    except RegionPair.DoesNotExist:
        if not create:
            return None, "No region pair found in database"

        ref1, ref2 = parse_img(img1), parse_img(img2)
        region_pair = RegionPair.objects.create(
            img_1=img1,
            img_2=img2,
            digit_1=ref1.digit,
            digit_2=ref2.digit,
            score=None,
            similarity_type=SimilarityType.AUTO,
            category_x=[],
        )
        return region_pair, "New region pair created"


def normalize_pair(img_1: str, img_2: str):
    img_1, img_2 = add_jpg(img_1), add_jpg(img_2)
    if img_2 < img_1:
        img_1, img_2 = img_2, img_1
    return img_1, img_2


def get_or_create_pair(img_1, img_2, create=True):
    img_1, img_2 = normalize_pair(img_1, img_2)

    pair = RegionPair.objects.filter(img_1=img_1, img_2=img_2).first()
    if pair:
        return pair, False

    if not create:
        return None, False

    ref1, ref2 = parse_img(img_1), parse_img(img_2)
    return (
        RegionPair(
            img_1=img_1,
            img_2=img_2,
            digit_1=ref1.digit,
            digit_2=ref2.digit,
            category=1,
            similarity_type=SimilarityType.PROPAGATED,
            score=None,
            category_x=[],
        ),
        True,
    )


F_IMG1, F_IMG2, F_D1, F_D2, F_ANNO1, F_ANNO2, F_SCORE, F_CAT, F_CATX, F_SIMTYPE = range(
    10
)

GZIP_BATCH_SIZE = 1000


def row_to_dict(row):
    return {
        "img_1": row[F_IMG1],
        "img_2": row[F_IMG2],
        "digit_1": row[F_D1],
        "digit_2": row[F_D2],
        "anno_1": row[F_ANNO1],
        "anno_2": row[F_ANNO2],
        "score": row[F_SCORE],
        "category": row[F_CAT],
        "category_x": row[F_CATX] or [],
        "similarity_type": row[F_SIMTYPE],
    }


def stream_pairs_ndjson(sql, params):
    """Generator yielding one JSON line per pair."""
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        for row in cursor:
            yield json.dumps(row_to_dict(row), separators=(",", ":")) + "\n"


def build_pairs_query(digit_ids, categories, min_score, max_score, topk, exclude_self):
    conditions = ["digit_1 = ANY(%s)", "digit_2 = ANY(%s)"]
    params = [list(digit_ids), list(digit_ids)]

    if min_score is not None:
        conditions.append("score >= %s")
        params.append(min_score)

    if max_score is not None:
        conditions.append("score <= %s")
        params.append(max_score)

    if exclude_self:
        conditions.append("digit_1 != digit_2")

    if categories:
        has_null = 0 in categories
        real_cats = [c for c in categories if c != 0]

        if has_null and real_cats:
            conditions.append("(category = ANY(%s) OR category IS NULL)")
            params.append(real_cats)
        elif has_null:
            conditions.append("category IS NULL")
        elif real_cats:
            conditions.append("category = ANY(%s)")
            params.append(real_cats)

    sql = f"""
        SELECT img_1, img_2, digit_1, digit_2, anno_1, anno_2,
               score, category, category_x, similarity_type
        FROM webapp_regionpair
        WHERE {" AND ".join(conditions)}
        ORDER BY score DESC NULLS FIRST
        {"LIMIT " + str(int(topk)) if topk else ""}
    """

    return sql, params
