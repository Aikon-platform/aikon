import os
from collections import defaultdict
from itertools import combinations_with_replacement
import numpy as np

import requests
from typing import List

from app.config.settings import EXAPI_URL, APP_URL, APP_NAME
from app.webapp.models.annotation import Annotation
from app.webapp.utils.functions import flatten_dict
from app.webapp.utils.iiif import gen_iiif_url
from app.webapp.utils.iiif.annotation import formatted_annotations
from app.webapp.utils.logger import log
from app.webapp.utils.paths import SCORES_PATH


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


def check_computed_pairs(anno_refs):
    sim_files = os.listdir(SCORES_PATH)
    anno_to_send = []
    for pair in doc_pairs(anno_refs):
        if f"{'-'.join(sorted(pair))}.npy" not in sim_files:
            anno_to_send.extend(pair)
    # return list of unique anno_ref involved in one of the pairs that are not already computed
    return list(set(anno_to_send))


def get_computed_pairs(anno_ref):
    return [
        pair_file.replace(".npy", "")
        for pair_file in os.listdir(SCORES_PATH)
        if anno_ref in pair_file
    ]


def get_anno_ref_in_pairs(pairs):
    return list(set([ref for pair in pairs for ref in pair.split("-")]))


def get_compared_annos(anno_ref):
    return get_anno_ref_in_pairs(get_computed_pairs(anno_ref))


def gen_img_ref(img, coord):
    return f"{img.split('.')[0]}_{coord}"


def get_annotation_urls(anno: Annotation):
    """
    {
        "wit1_man191_0009_166,1325,578,516": ""https://eida.obspm.fr/iiif/2/wit1_man191_0009.jpg/166,1325,578,516/full/0/default.jpg"",
        "wit1_man191_0027_1143,2063,269,245": "https://eida.obspm.fr/iiif/2/wit1_man191_0027.jpg/1143,2063,269,245/full/0/default.jpg",
        "wit1_man191_0031_857,2013,543,341": "https://eida.obspm.fr/iiif/2/wit1_man191_0031.jpg/857,2013,543,341/full/0/default.jpg",
        "img_name": "..."
    }
    """
    folio_anno = []

    _, canvas_annos = formatted_annotations(anno)
    for canvas_nb, annos, img_name in canvas_annos:
        if len(annos):
            folio_anno.append(
                {
                    gen_img_ref(img_name, a[0]): gen_iiif_url(
                        img_name, 2, f"{a[0]}/full/0"
                    )
                    for a in annos
                }
            )

    return flatten_dict(folio_anno)


def gen_list_url(anno_ref):
    return f"{APP_URL}/{APP_NAME}/{anno_ref}/list"


def similarity_request(annos: List[Annotation]):
    documents = {ref: gen_list_url(ref) for ref in [anno.get_ref() for anno in annos]}

    try:
        response = requests.post(
            url=f"{EXAPI_URL}/similarity/start",
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
                    "url": f"{EXAPI_URL}/similarity/start",
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
    annos: List[Annotation],
    checked_anno_ref: str,
    anno_refs: List[str] = None,
    max_rows: int = 50,
    show_checked_ref: bool = False,
):
    total_scores = defaultdict(list)
    img_names = defaultdict(set)
    prefix_key = "_".join(checked_anno_ref.split("_")[:2])
    topk = 10

    if anno_refs is None:
        anno_refs = [anno.get_ref() for anno in annos]

    for pair in doc_pairs(anno_refs):
        try:
            score_path_pair = f"{SCORES_PATH}/{'-'.join(sorted(pair))}.npy"
            if prefix_key not in score_path_pair:
                continue
            pair_scores = load_npy_file(score_path_pair)
        except FileNotFoundError as e:
            # TODO: trigger similarity request?
            log(f"[compute_total_similarity] no score file for {pair}", e)
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


def reset_similarity(anno_ref):
    # TODO function to delete all similarity files concerning the anno_ref
    # TODO send request to delete features and scores concerning the anno ref as well
    pass
