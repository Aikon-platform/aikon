import os
import requests

from pathlib import Path
from django.db import transaction
from django.db.models import Q, F
from typing import Tuple, Dict, Set, List
from collections import defaultdict, Counter
from itertools import combinations_with_replacement
import numpy as np

from heapq import nlargest
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

from app.similarity.const import SCORES_PATH
from app.config.settings import CV_API_URL, APP_URL, APP_NAME
from app.similarity.models.region_pair import RegionPair
from app.webapp.models.regions import Regions
from app.webapp.utils.logger import log
from app.webapp.views import check_ref


@lru_cache(maxsize=None)
def load_npy_file(score_path):
    try:
        return np.load(score_path, allow_pickle=True)
    except FileNotFoundError as e:
        log(f"[load_npy_file] no score file for {score_path}", e)
        return None


def score_file_to_db(score_path):
    """
    Load scores from a .npy file and add all of its pairs in the RegionPair table
    If pair already exists, only score is updated
    """
    pair_scores = load_npy_file(score_path)
    if pair_scores is None:
        return False

    # regions ref
    ref_1, ref_2 = Path(score_path).stem.split("-")

    pairs_to_update = []
    try:
        for score, img1, img2 in pair_scores:
            pairs_to_update.append(
                RegionPair(
                    img_1=img1,
                    img_2=img2,
                    score=float(score),
                    regions_id_1=ref_1.split("_anno")[1],
                    regions_id_2=ref_2.split("_anno")[1],
                    is_manual=False,
                    category_x=[],
                )
            )
    except ValueError as e:
        log(f"[score_file_to_db] error while processing {score_path}", e)
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
        log(f"[score_file_to_db] error while adding pairs to db {score_path}", e)
        return False

    log(f"Processed {len(pair_scores)} pairs from {score_path}")
    return True


def get_region_pairs_with(q_img, include_self=False):
    """
    Retrieve all RegionPair records containing the given query image name

    :param q_img: str, the image name to look for
    :param include_self: bool, if we consider comparisons of the region with itself
    :return: list of RegionPair objects
    """
    query = Q(img_1=q_img) | Q(img_2=q_img)

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
    )

    associated_ids = set()
    for pair in pairs:
        associated_ids.add(
            int(pair.regions_id_2)
            if int(pair.regions_id_1) == regions_id
            else int(pair.regions_id_1)
        )

    return list(associated_ids)


def get_regions_q_imgs(regions_id: int):
    """
    Retrieve all images associated with a given regions_id from RegionPair records.

    :param regions_id: int, the regions_id to look for
    :return: list of image names associated with the regions_id
    """
    pairs = RegionPair.objects.filter(
        Q(regions_id_1=regions_id) | Q(regions_id_2=regions_id)
    )
    result_imgs = []
    for pair in pairs:
        if int(pair.regions_id_1) == regions_id:
            result_imgs.append(pair.img_1)
        elif int(pair.regions_id_2) == regions_id:
            result_imgs.append(pair.img_2)

    return list(set(result_imgs))


def get_best_pairs(
    q_img: str,
    region_pairs: List[RegionPair],
    excluded_categories: List[int],
    topk: int,
    user_id: int = None,
) -> List[Set[Tuple[str, float, int, List[int]]]]:
    """
    Process RegionPair objects and return a structured dictionary.

    :param region_pairs: List of RegionPair objects
    :param q_img: Query image name
    :param excluded_categories: List of category numbers to exclude
    :param topk: Number of top scoring pairs to include
    :param user_id: int ID of the user asking for similarities
    :return: List with structured data
    """
    best_pairs = []
    manual_pairs = []
    pairs = []

    for pair in region_pairs:
        # pair_data = (score, q_img, s_img, q_regions, s_regions, category, category_x, is_manual)
        pair_data = pair.get_info(q_img)

        if pair.category not in excluded_categories:
            if pair.is_manual:
                manual_pairs.append(pair_data)
            elif len(pair.category_x or []) > 0 and user_id in pair.category_x:
                manual_pairs.append(pair_data)
            else:
                pairs.append(pair_data)

    # All manual pairs are added
    best_pairs += manual_pairs

    # Sort pairs by score in descending order and add top k
    pairs.sort(key=lambda x: x[0], reverse=True)
    best_pairs += pairs[:topk]

    return best_pairs


def process_score_file(score_path, q_prefix, page_imgs):
    # SOON TO BE NOT USED
    pair_scores = load_npy_file(score_path)
    if pair_scores is None:
        return None

    img_scores = defaultdict(Counter)
    for score, img1, img2 in pair_scores:
        if img1.startswith(q_prefix) and img1 in page_imgs:
            img_scores[img1][img2] = max(img_scores[img1][img2], float(score))
        elif img2.startswith(q_prefix) and img2 in page_imgs:
            img_scores[img2][img1] = max(img_scores[img2][img1], float(score))

    return img_scores


def get_imgs_in_file(score_path, q_prefix):
    # SOON TO BE NOT USED
    pair_scores = load_npy_file(score_path)
    if pair_scores is None:
        return set()

    q_imgs = set()
    for _, img1, img2 in pair_scores:
        if img1.startswith(q_prefix):
            q_imgs.add(img1)
        elif img2.startswith(q_prefix):
            q_imgs.add(img2)

    return q_imgs


def get_imgs_in_score_files(pairs: List[str], q_prefix: str):
    # SOON TO BE NOT USED
    """
    Get all images names beginning with q_prefix in the scores files for the given pairs,
    Thus retrieving only image names from the same document
    """
    all_q_imgs = set()
    with ThreadPoolExecutor() as executor:
        futures = []
        for pair in pairs:
            score_path = f"{SCORES_PATH}/{pair}.npy"
            futures.append(executor.submit(get_imgs_in_file, score_path, q_prefix))

        for future in futures:
            all_q_imgs.update(future.result())
    return sorted(all_q_imgs)


def compute_page_scores(
    q_regions: Regions,
    sim_regions: List[Regions],
    include_q_regions=False,
    page_nb=1,
    page_len=50,
    page_q_imgs=None,
    topk=10,
):
    # SOON TO BE NOT USED
    q_prefix = q_regions.get_digit().get_ref()
    q_ref = q_regions.get_ref()
    sim_refs = [regions.get_ref() for regions in sim_regions]
    if include_q_regions:
        sim_refs += [q_ref]

    pairs = ["-".join(sorted((q_ref, sim_ref))) for sim_ref in sim_refs]

    if page_q_imgs is None:
        all_q_imgs = get_imgs_in_score_files(pairs, q_prefix)
        start_idx = (page_nb - 1) * page_len
        end_idx = start_idx + page_len
        page_q_imgs = set(all_q_imgs[start_idx:end_idx])

    total_scores = defaultdict(Counter)
    with ThreadPoolExecutor() as executor:
        futures = []
        for pair in pairs:
            score_path = f"{SCORES_PATH}/{pair}.npy"
            futures.append(
                executor.submit(process_score_file, score_path, q_prefix, page_q_imgs)
            )

        for future in futures:
            result = future.result()
            if result:
                for img_name, scores in result.items():
                    total_scores[img_name].update(scores)

    # Get top k scores for each query image
    result = {
        q_img: nlargest(topk, scores.items(), key=lambda x: x[1])
        for q_img, scores in total_scores.items()
    }

    return dict(sorted(result.items(), key=lambda x: x[0]))


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


def gen_list_url(regions_ref):
    return f"{APP_URL}/{APP_NAME}/{regions_ref}/list"


def similarity_request(regions: List[Regions]):
    documents = {
        ref: gen_list_url(ref) for ref in [region.get_ref() for region in regions]
    }

    try:
        response = requests.post(
            url=f"{CV_API_URL}/similarity/start",
            json={
                "documents": documents,
                # "model": f"{FEAT_BACKBONE}",
                "callback": f"{APP_URL}/{APP_NAME}/similarity",
            },
        )
        if response.status_code == 200:
            log(f"[similarity_request] Similarity request send: {response.text or ''}")
            return True
        else:
            error = {
                "source": "[similarity_request]",
                "error_message": f"Request failed for {list(documents.keys())} with status code: {response.status_code}",
                "request_info": {
                    "method": "POST",
                    "url": f"{CV_API_URL}/similarity/start",
                    "payload": {
                        "documents": documents,
                        "callback": f"{APP_URL}/{APP_NAME}/similarity",
                    },
                },
                "response_info": {
                    "status_code": response.status_code,
                    "text": response.text or "",
                },
            }

            log(error)
            return False
    except Exception as e:
        log(f"[similarity_request] Request failed for {list(documents.keys())}", e)

    return False


def load_similarity(pair):
    try:
        pair_scores = np.load(
            SCORES_PATH / f"{'-'.join(sorted(pair))}.npy", allow_pickle=True
        )
        return pair, pair_scores
    except FileNotFoundError as e:
        log(f"[load_similarity] no score file for {pair}", e)
        return pair, None


def compute_total_similarity(
    regions: List[Regions],
    checked_regions_ref: str,
    regions_refs: List[str] = None,
    max_rows: int = 50,
    show_checked_ref: bool = False,
):
    # Soon to be NOT USED
    total_scores = defaultdict(list)
    img_names = defaultdict(set)
    prefix_key = "_".join(checked_regions_ref.split("_")[:2])
    topk = 10

    if regions_refs is None:
        regions_refs = [region.get_ref() for region in regions]

    for pair in doc_pairs(regions_refs):
        try:
            score_path = f"{SCORES_PATH}/{'-'.join(sorted(pair))}.npy"
            if prefix_key not in score_path:
                continue
            pair_scores = load_npy_file(score_path)
        except FileNotFoundError as e:
            # TODO: trigger similarity request?
            log(f"[compute_total_similarity] no score file for {pair}", e)
            continue

        if pair_scores is None:
            log(f"[compute_total_similarity] no score for {pair}")
            continue

        # Create a dictionary with image names as keys and scores as values
        img_scores = defaultdict(set)
        for score, img1, img2 in pair_scores:
            if img2 not in img_names[img1]:
                img_scores[img1].add((float(score), img2))
                img_names[img1].add(img2)
            if img1 not in img_names[img2]:
                img_scores[img2].add((float(score), img1))
                img_names[img2].add(img1)

        # Update total scores
        for img_name, scores in img_scores.items():
            if img_name.startswith(prefix_key):
                total_scores[img_name].extend(scores)

    # Filter out items starting with prefix key
    if not show_checked_ref:
        for q_img in total_scores:
            total_scores[q_img] = [
                item
                for item in total_scores[q_img]
                if not item[1].startswith(prefix_key)
            ]

    # Sort scores for each query image in descending order and keep top 10
    total_scores = {
        q_img: sorted(scores, key=lambda x: x[0], reverse=True)[:topk]
        for q_img, scores in total_scores.items()
    }

    # Sort rows based on the first score of image
    sorted_total_scores = dict(
        sorted(total_scores.items(), key=lambda x: x[1], reverse=True)
    )

    # Limit number of rows to max_rows
    return {k: sorted_total_scores[k] for k in list(sorted_total_scores)[:max_rows]}


def reset_similarity(regions_ref):
    # TODO function to delete all similarity files concerning the regions_ref
    # TODO send request to delete features and scores concerning the anno ref as well
    pass
