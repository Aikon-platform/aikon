import os
from collections import defaultdict
from itertools import combinations_with_replacement
import numpy as np

import requests
from typing import List

from app.similarity.const import SCORES_PATH
from app.config.settings import CV_API_URL, APP_URL, APP_NAME
from app.webapp.models.regions import Regions
from app.webapp.utils.logger import log


def load_npy_file(score_path_pair):
    try:
        return np.load(score_path_pair, allow_pickle=True)
    except FileNotFoundError as e:
        log(f"[load_npy_file] no score file for {score_path_pair}", e)
        return None


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


def get_compared_regions(regions_ref):
    return get_regions_ref_in_pairs(get_computed_pairs(regions_ref))


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


def check_score_files(file_names):
    from app.webapp.tasks import check_similarity_files

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


def compute_total_similarity(
    regions: List[Regions],
    checked_regions_ref: str,
    regions_refs: List[str] = None,
    max_rows: int = 50,
    show_checked_ref: bool = False,
):
    total_scores = defaultdict(list)
    img_names = defaultdict(set)
    prefix_key = "_".join(checked_regions_ref.split("_")[:2])
    topk = 10

    if regions_refs is None:
        regions_refs = [region.get_ref() for region in regions]

    for pair in doc_pairs(regions_refs):
        try:
            score_path_pair = f"{SCORES_PATH}/{'-'.join(sorted(pair))}.npy"
            if prefix_key not in score_path_pair:
                continue
            pair_scores = load_npy_file(score_path_pair)
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
    sorted_total_scores = {
        k: sorted_total_scores[k] for k in list(sorted_total_scores)[:max_rows]
    }

    return sorted_total_scores


def reset_similarity(regions_ref):
    # TODO function to delete all similarity files concerning the regions_ref
    # TODO send request to delete features and scores concerning the anno ref as well
    pass
