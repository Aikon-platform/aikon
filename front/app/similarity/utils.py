import hashlib
import json
import os
import re

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
from app.webapp.models.digitization import Digitization
from app.webapp.models.regions import Regions
from app.webapp.models.witness import Witness
from app.webapp.utils import tasking
from app.webapp.utils.functions import extract_nb, sort_key
from app.webapp.utils.logger import log
from app.webapp.views import check_ref


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
            # TODO add options for similarity
            # "algorithm": "algorithm",
            # "feat_net": "model.pt",
            # "feat_set": "set",
            # "feat_layer": "layer",
            # "segswap_prefilter": true, # if algorithm is "segswap"
            # "segswap_n": 0, # if algorithm is "segswap"
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
                continue

            with open(score_file, "wb") as f:
                json_content["result_url"] = score_url
                f.write(orjson.dumps(json_content))

        except Exception as e:
            log(f"Could not download similarity scores from {score_url}", e)
            continue

        try:
            process_similarity_file.delay(str(score_file))
        except Exception as e:
            log(f"Could not process similarity scores from {score_url}", e)
            raise e
    return


def prepare_document(document: Witness | Digitization | Regions, **kwargs):
    regions = document.get_regions() if hasattr(document, "get_regions") else [document]

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


@lru_cache(maxsize=None)
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


@lru_cache(maxsize=None)
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

    images = [img.get("id") for img in json_scores["index"].get("images")]

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
                        # algorithm=algo,
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
                ["score", "regions_id_1", "regions_id_2", "is_manual"],
                ["img_1", "img_2"],
                "score",
            )
    except Exception as e:
        log(f"[score_file_to_db] error while adding pairs to db {pair_ref}", e)
        return False

    log(f"Processed {len(pair_scores)} pairs from {pair_ref}")
    return True


def get_region_pairs_with(q_img, regions_ids, include_self=False, strict=False):
    """
    Retrieve all RegionPair records containing the given query image name

    :param q_img: str, the image name to look for
    :param regions_ids: list, ids of regions that should be included in the pairs (regions_id_1 or regions_id_2)
    :param include_self: bool, if we consider comparisons of the region with itself
    :param strict: bool, ensures that `regions_ids` is used to filter the similarity image, not the query image (`q_img`): the matched image's regions, must be in `regions_ids`
    :return: list of RegionPair objects
    """
    if not strict:
        query = Q(img_1=q_img) | Q(img_2=q_img)
        query &= Q(regions_id_1__in=regions_ids) | Q(regions_id_2__in=regions_ids)
    else:
        query = (Q(img_1=q_img) & Q(regions_id_2__in=regions_ids)) | (
            Q(img_2=q_img) & Q(regions_id_1__in=regions_ids)
        )

    if not include_self:
        query &= ~Q(regions_id_1=F("regions_id_2"))

    return list(RegionPair.objects.filter(query))


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
    Retrieve all RegionPair records containing the given query image name and the given regions_id
    if q_img is in img_1, then s_regions_id should be in regions_id_2 and vice versa
    :param q_img: str, the image name to look for
    :param s_regions_id: int, the regions_id to look for
    :return: list of RegionPair objects
    """
    return RegionPair.objects.filter(
        (Q(img_1=q_img) & Q(regions_id_2=s_regions_id))
        | (Q(img_2=q_img) & Q(regions_id_1=s_regions_id))
    )


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
    excluded_categories: List[int],
    topk: int,
    user_id: int = None,
) -> List[Set[RegionPairTuple]]:
    """
    Process RegionPair objects and return a structured dictionary.

    :param region_pairs: List of RegionPair objects
    :param q_img: Query image name
    :param excluded_categories: List of category numbers to exclude
    :param topk: Number of top scoring pairs to include
    :param user_id: int ID of the user asking for similarities
    :return: List with structured data
    """
    manual_pairs = []
    propagated_pairs = []  # propagated pairs that have been saved to database
    auto_pairs = []
    added_pairs = set()

    for pair in region_pairs:
        if pair.category not in excluded_categories:
            pair_data = pair.get_info(q_img)
            pair_ref = pair.get_ref()

            if pair_ref in added_pairs:
                continue
            added_pairs.add(pair_ref)

            if (
                pair.is_manual
                or pair.similarity_type == 2
                or (pair.category_x and user_id in pair.category_x)
            ):
                manual_pairs.append(pair_data)
            elif pair.similarity_type == 3:
                propagated_pairs.append(pair_data)
            else:
                auto_pairs.append(pair_data)

    auto_pairs.sort(key=lambda x: x[0], reverse=True)
    return manual_pairs + propagated_pairs + auto_pairs[:topk]


def validate_img_ref(img_string):
    # wit<id>_<digit><id>_<canvas_nb>_<x>,<y>,<h>,<w>
    pattern = r"^wit\d+_[a-zA-Z]{3}\d+_\d+_\d+,\d+,\d+,\d+$"
    return bool(re.match(pattern, img_string))


def parse_img_ref(img_string):
    # wit<id>_<digit><id>_<canvas_nb>_<x>,<y>,<h>,<w>.jpg
    wit, digit, canvas, coord = img_string.split("_")
    return {
        "wit": extract_nb(wit),
        "digit": extract_nb(digit),
        "canvas": canvas,
        "coord": coord.split(".")[0].split(","),
    }


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

    # TODO check similarity file content inside a celery task
    check_similarity_files.delay(file_names)


def load_similarity(pair):
    try:
        pair_scores = np.load(
            SCORES_PATH / f"{'-'.join(sorted(pair))}.npy", allow_pickle=True
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
            try:
                os.remove(os.path.join(SCORES_PATH, file))
            except OSError as e:
                log(f"[reset_similarity] Error removing file {file}", e)

    try:
        delete_pairs_with_regions(regions_id)
    except Exception as e:
        log(f"[reset_similarity] Error deleting pairs with region id {regions_id}", e)

    # TODO send request to delete features and scores concerning the anno ref as well
    return True
