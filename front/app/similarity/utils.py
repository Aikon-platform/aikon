import hashlib
import json
import os
import re
from enum import IntEnum

import numpy as np
from typing import Tuple, Set, List

import orjson
import requests
from itertools import combinations_with_replacement
from functools import lru_cache

from pathlib import Path
from django.db import transaction
from django.db.models import Q, F
from django.core.cache import cache

from app.similarity.const import SCORES_PATH
from app.config.settings import APP_URL, APP_NAME
from app.similarity.models.region_pair import RegionPair, RegionPairTuple
from app.similarity.tasks import delete_api_similarity
from app.webapp.models.digitization import Digitization
from app.webapp.models.regions import Regions
from app.webapp.models.witness import Witness
from app.webapp.utils import tasking
from app.webapp.utils.functions import sort_key, delete_path
from app.webapp.utils.logger import log
from app.webapp.views import check_ref
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


################################################################
# ⚠️   prepare_request() & process_results() are mandatory  ⚠️ #
# ⚠️ function used by Treatment to generate request payload ⚠️ #
# ⚠️    and save results files when sends back by the API   ⚠️ #
################################################################


def prepare_request(witnesses, treatment_id):
    return tasking.prepare_request(
        witnesses,
        treatment_id,
        prepare_document,
        "similarity",
        {
            # NOTE api parameters are added in similarity.forms.get_api_parameters
        },
    )


def generate_hash(params):
    serialized = json.dumps(params, sort_keys=True)
    return hashlib.sha256(serialized.encode()).hexdigest()[:8]


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

        try:
            response = requests.get(score_url, stream=True)
            response.raise_for_status()
            json_content = response.json()

            param_hash = generate_hash(json_content.get("parameters", {}))
            score_file = Path(f"{SCORES_PATH}/{regions_ref_pair}/{param_hash}.json")
            os.makedirs(f"{SCORES_PATH}/{regions_ref_pair}", exist_ok=True)
            if score_file.exists():
                # This check should be made when starting the task not now
                log(f"File {score_file} already exists, overriding its content")
                # continue

            with open(score_file, "wb") as f:
                json_content["result_url"] = score_url
                f.write(orjson.dumps(json_content))

        except Exception as e:
            log(f"Could not download similarity scores from {score_url}", e)
            continue

        try:
            # process_similarity_file task calls score_file_to_db()
            process_similarity_file.delay(str(score_file))
        except Exception as e:
            log(f"Could not process similarity scores from {score_url}", e)
            raise e
    return


def prepare_document(document: Witness | Digitization | Regions, **kwargs):
    regions = document.get_regions() if hasattr(document, "get_regions") else [document]

    if not regions:
        # TODO should task be canceled because one of the document has no extraction??
        raise ValueError(
            f"“{document}” has no extracted regions for which to calculate similarity scores"
            if APP_LANG == "en"
            else f"« {document} » n'a pas de régions extraites pour lesquelles calculer les scores de similarité"
        )

    return [
        {"type": "url_list", "src": f"{APP_URL}/{APP_NAME}/{ref}/list", "uid": ref}
        for ref in [region.get_ref() for region in regions]
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

    images = [f'{img.get("id")}.jpg' for img in json_scores["index"].get("images")]

    return [
        (float(pair[2]), images[pair[0]], images[pair[1]])
        for pair in json_scores["pairs"]
    ]


def score_file_to_db(file_path):
    """
    Load scores from a .json file and add all of its pairs in the RegionPair table
    If pair already exists, only score is updated
    """
    p = Path(file_path)
    pair_scores = load_scores(p)
    pair_ref, algo = p.parent.name, p.stem
    if not pair_scores or not pair_ref:
        return False

    ref_1, ref_2 = sorted(pair_ref.split("-"), key=sort_key)
    # TODO verify that regions_id exists?

    pairs_to_update = []
    try:
        for score, img1, img2 in pair_scores:
            img1, img2 = sorted([img1, img2], key=sort_key)
            score = float(score)
            if score > 0:
                pairs_to_update.append(
                    RegionPair(
                        img_1=img1,
                        img_2=img2,
                        score=score,
                        regions_id_1=ref_1.split("_anno")[1],
                        regions_id_2=ref_2.split("_anno")[1],
                        is_manual=False,
                        similarity_type=1,
                        category_x=[],
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
                [
                    "score",
                    "regions_id_1",
                    "regions_id_2",
                    "is_manual",
                    "similarity_type",
                ],
                ["img_1", "img_2"],
                "score",
            )
    except Exception as e:
        log(f"[score_file_to_db] error while adding pairs to db {pair_ref}", e)
        return False

    log(f"Processed {len(pair_scores)} pairs from {pair_ref}")
    return True


def get_compared_regions_ids(regions_id):
    """
    Retrieve all unique region IDs that have been associated with the given region ID in RegionPair records.

    :param regions_id: str, the region ID to look for
    :return: list of unique region IDs
    """
    pairs = RegionPair.objects.filter(
        Q(regions_id_1=regions_id) | Q(regions_id_2=regions_id)
    ).values_list("regions_id_1", "regions_id_2")

    associated_ids = set()
    for id1, id2 in pairs:
        associated_ids.add(int(id2) if int(id1) == regions_id else int(id1))

    return list(associated_ids)


def get_regions_pairs(regions_id: int):
    return RegionPair.objects.filter(
        Q(regions_id_1=regions_id) | Q(regions_id_2=regions_id)
    ).values_list("regions_id_1", "regions_id_2", "img_1", "img_2")


def get_matched_regions(q_img: str, s_regions_id: int):
    """
    Retrieve all RegionPair records containing the given query image name and the given s_regions_id
    if q_img is in img_1, then s_regions_id should be in regions_id_2 and vice versa
    :param q_img: str, the image name to look for
    :param s_regions_id: int, the regions_id to look for
    :return: list of RegionPair objects
    """
    return RegionPair.objects.filter(
        (Q(img_1=q_img) & Q(regions_id_2=s_regions_id))
        | (Q(img_2=q_img) & Q(regions_id_1=s_regions_id))
    )


def get_region_pairs_with(q_img, query_regions_ids, target_regions_ids):
    """
    Retrieve RegionPair records where:
    - One image is q_img
    - One region is from query_regions_ids
    - The other region is from target_regions_ids

    :param q_img: str, the query image name
    :param query_regions_ids: list[int], IDs of query regions
    :param target_regions_ids: list[int], IDs of target regions to compare against
    :return: List of RegionPair objects
    """
    # Query where q_img is img_1 and its region is in query_regions_ids
    # and the comparison region is in target_regions_ids
    query1 = (
        Q(img_1=q_img)
        & Q(regions_id_1__in=query_regions_ids)
        & Q(regions_id_2__in=target_regions_ids)
    )

    # Query where q_img is img_2 and its region is in query_regions_ids
    # and the comparison region is in target_regions_ids
    query2 = (
        Q(img_2=q_img)
        & Q(regions_id_2__in=query_regions_ids)
        & Q(regions_id_1__in=target_regions_ids)
    )

    # Note: if img1 and img2 are not correctly paired with regions_id_1 and regions_id_2,
    #       they will be excluded from results

    query = query1 | query2

    # if there is no intersection between query and target regions, remove self-comparisons
    if not bool(set(query_regions_ids) & set(target_regions_ids)):
        query &= ~Q(regions_id_1=F("regions_id_2"))

    return list(RegionPair.objects.filter(query))


def get_pairs_for_regions(unfiltered_pairs, q_rid, regions_ids):
    """For a given regions identifier, filters a list of pairs that relates to it, then
    NOT USED
    keeps only those pertaining to the selected comparison regions.

    :param unfiltered_pairs: list of RegionPair objects
    :param q_rid: in - id of the Regions object currently analyzed
    :param regions_ids: list[int] - ids of the Regions objects to be linked by pairs to the Regions identified by q_rid
    :return: list of RegionPair objects with one end from the Regions  identifier by q_rid and one end from any Regions identified by regions_ids
    """
    pairs = [
        pair
        for pair in unfiltered_pairs
        if pair.regions_id_1 == q_rid or pair.regions_id_2 == q_rid
    ]
    if q_rid not in regions_ids:
        pairs = [pair for pair in pairs if pair.regions_id_1 != pair.regions_id_2]

    return pairs


def delete_pairs_with_regions(regions_id: int):
    RegionPair.objects.filter(
        Q(regions_id_1=regions_id) | Q(regions_id_2=regions_id)
    ).delete()

    if cache.get(f"regions_q_imgs_{regions_id}") is not None:
        cache.delete(f"regions_q_imgs_{regions_id}")


def get_regions_q_imgs(regions_id: int, witness_id=None, cached=False):
    """
    Retrieve all images associated with a given regions_id from RegionPair records.

    :param regions_id: int, the regions_id to look for
    :param witness_id: int, the id of the witness linked to the regions
    :param cached: bool, whether to cache the result
    :return: list of image names associated with the regions_id
    """
    cache_key = f"regions_q_imgs_{regions_id}"
    if cached:
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result

    if witness_id is None:
        img_1_list = list(
            RegionPair.objects.filter(regions_id_1=regions_id).values_list(
                "img_1", flat=True
            )
        )

        img_2_list = list(
            RegionPair.objects.filter(regions_id_2=regions_id).values_list(
                "img_2", flat=True
            )
        )
        result = list(set(img_1_list + img_2_list))
    else:
        # NOTE workaround for incorrectly inserted RegionPairs (where regions_id_1 and img_1 do not match)
        from itertools import chain

        img_1_list = chain(
            *RegionPair.objects.filter(regions_id_1=regions_id).values_list(
                "img_1", "img_2"
            )
        )
        img_2_list = chain(
            *RegionPair.objects.filter(regions_id_2=regions_id).values_list(
                "img_1", "img_2"
            )
        )

        result = [
            img
            for img in set(img_1_list) | set(img_2_list)
            if img.startswith(f"wit{witness_id}_")
        ]

    if cached:
        cache.set(cache_key, result, timeout=3600)  # Cache for 1 hour

    return result


def get_best_pairs(
    q_img: str,
    region_pairs: List[RegionPair],
    excluded_categories: Set[int],
    topk: int | None = None,
    user_id: int | None = None,
    export: bool = False,
) -> List[Set[RegionPairTuple]]:
    """
    Process RegionPair objects and return a list.

    :param q_img: Query image name
    :param region_pairs: List of RegionPair objects
    :param excluded_categories: List of category numbers to exclude
    :param topk: Number of top scoring pairs to include (None = all)
    :param user_id: int ID of the user asking for similarities
    :param export: boolean value - when building pair for export, no sorting & no threshold
    :return: List with structured data
    """
    manual_pairs = []
    propagated_pairs = []  # propagated pairs that have been saved to database
    categorized_pairs = []  # where category is not null
    auto_pairs = []
    auto_pairs_no_score = []
    nomatch_pairs = []  # category == 4
    added_images = set()
    export_pairs = []  # pairs for export: all in big a single big list
    export_pairs_no_score = []  # pairs for export without a score

    for pair in region_pairs:
        # [score, img1, img2, regions_id1, regions_id2, category, is_manual, similarity_type]
        pair_data = pair.get_info(q_img)
        if pair_data[2] in added_images:
            # NOTE: first duplicate wins. Higher-priority pairs (e.g., manual) appearing later
            #    will be discarded if lower-priority pairs (e.g., auto) were seen first.
            continue
        added_images.add(pair_data[2])

        if export:
            if pair.score is not None:
                export_pairs.append(pair_data)
            else:
                export_pairs_no_score.append(pair_data)
            continue

        if pair.category in excluded_categories:
            continue

        if (
            pair.is_manual
            or pair.similarity_type == SimilarityType.MANUAL
            or (pair.category_x and user_id in pair.category_x)
        ):
            manual_pairs.append(pair_data)
        elif pair.similarity_type == SimilarityType.PROPAGATED:
            propagated_pairs.append(pair_data)
        elif pair.category == SimilarityCategory.NO_MATCH:
            nomatch_pairs.append(pair_data)
        elif pair.category is not None:
            categorized_pairs.append(pair_data)
        elif pair.score is not None:
            auto_pairs.append(pair_data)
        else:
            auto_pairs_no_score.append(pair_data)

    if export:
        # sort by score, descending, finish with pairs with no score.
        return (
            sorted(export_pairs, key=lambda x: x[0], reverse=True)
            + export_pairs_no_score
        )

    categorized_pairs.sort(key=lambda x: x[5])  # sort by category number, ascending

    # sort by score, descending, finish with pairs with no score.
    auto_pairs = (
        sorted(auto_pairs, key=lambda x: x[0], reverse=True) + auto_pairs_no_score
    )

    if topk:
        auto_pairs = auto_pairs[:topk]

    return (
        manual_pairs
        + propagated_pairs
        + categorized_pairs
        + auto_pairs
        + nomatch_pairs  # limit number of nomatch pairs?
    )


def validate_img_ref(img_string):
    # wit<id>_<digit><id>_<canvas_nb>_<x>,<y>,<h>,<w>
    pattern = r"^wit\d+_[a-zA-Z]{3}\d+_\d+_\d+,\d+,\d+,\d+$"
    return bool(re.match(pattern, img_string))


def doc_pairs(doc_ids: list):
    if isinstance(doc_ids, list) and len(doc_ids) > 0:
        return list(combinations_with_replacement(doc_ids, 2))
    raise ValueError("Input must be a non-empty list of ids.")


def check_computed_pairs(regions_refs):
    sim_files = os.listdir(SCORES_PATH)
    regions_to_send = []
    for pair in doc_pairs(regions_refs):
        if f"{'-'.join(sorted(pair))}.npy" not in sim_files:
            regions_to_send.extend(pair)
    # return list of unique regions_ref involved in one of the pairs that are not already computed
    return list(set(regions_to_send))


def get_computed_pairs(regions_ref):
    return [
        pair_file.replace(".npy", "")
        for pair_file in os.listdir(SCORES_PATH)
        if regions_ref in pair_file
    ]


def get_all_pairs():
    return [pair_file.replace(".npy", "") for pair_file in os.listdir(SCORES_PATH)]


def get_regions_ref_in_pairs(pairs):
    return list(set([ref for pair in pairs for ref in pair.split("-")]))


def get_compared_regions_refs(regions_ref):
    refs = get_regions_ref_in_pairs(get_computed_pairs(regions_ref))
    refs.remove(regions_ref)
    return refs


def get_compared_regions(regions: Regions):
    refs = get_compared_regions_refs(regions.get_ref())
    return [
        region
        for (passed, region) in [check_ref(ref, "Regions") for ref in refs]
        if passed
    ]


def check_score_files(file_names):
    from app.similarity.tasks import check_similarity_files

    # TODO check similarity file content inside a celery task (task is empty)
    check_similarity_files.delay(file_names)


def load_similarity(pair):
    try:
        pair_scores = np.load(
            Path(SCORES_PATH) / f"{'-'.join(sorted(pair))}.npy", allow_pickle=True
        )
        return pair, pair_scores
    except FileNotFoundError as e:
        log(f"[load_similarity] no score file for {pair}", e)
        return pair, None


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
        delete_pairs_with_regions(regions_id)
    except Exception as e:
        log(f"[reset_similarity] Error deleting pairs with region id {regions_id}", e)

    return True


def regions_from_img(q_img: str) -> int:
    """
    retrieve the regions id (member of `RegionPair.(regions_id_1|regions_id_2)`)
    for an image q_img (member of `RegionPair.(img_1|img_2)`).
    union.first() raises an error so we run 2 queries instead
    returns the ID of the regions object associated with the image.
    """
    if not q_img.endswith(".jpg"):
        q_img = f"{q_img}.jpg"

    q1 = RegionPair.objects.values_list("regions_id_1").filter(img_1=q_img).first()
    if q1:
        return q1[0]
    q2 = RegionPair.objects.values_list("regions_id_2").filter(img_2=q_img).first()
    if q2:
        return q2[0]

    def get_digit_id(img):
        return int(re.findall(r"\d+", img)[1])

    def get_digit_regions_id(digit_id):
        try:
            digit = Digitization.objects.get(id=digit_id)
        except Digitization.DoesNotExist:
            log(
                f"[get_regions_from_digit] Digitization with id {digit_id} does not exist"
            )
            digit = None
        regions = list(digit.get_regions() if digit else [])
        if not regions:
            regions = Regions.objects.create(
                digitization=digit,
                model="manual",
            )
        else:
            regions = regions[0]
        return int(regions.id)

    return get_digit_regions_id(get_digit_id(q_img))


def add_user_to_category_x(region_pair: RegionPair, user_id: int):
    if region_pair.category_x is None:
        region_pair.category_x = [user_id]
    elif user_id not in region_pair.category_x:
        region_pair.category_x.append(user_id)
    region_pair.category_x = [c for c in region_pair.category_x if c is not None]
    return region_pair
