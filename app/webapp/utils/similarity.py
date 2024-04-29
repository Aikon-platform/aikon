import hashlib
import os
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


def get_best_matches(img_scores, topk=10):
    sorted_scores = sorted(img_scores, key=lambda x: x[0], reverse=True)
    seen_images = set()
    for i in range(topk):
        if not i < len(sorted_scores):
            break
        score, image = sorted_scores[i]
        if image in seen_images:
            # Remove the tuple with the lowest score
            sorted_scores.pop(i)
            break
        seen_images.add(image)

    # Check for duplicates again until all topk tuples have unique images
    while len(set(image for _, image in sorted_scores[:topk])) != topk:
        for i in range(topk):
            if not i < len(sorted_scores):
                break
            score, image = sorted_scores[i]
            if image in seen_images:
                # If duplicate, remove the tuple with the lowest score
                sorted_scores.pop(i)
                break
            seen_images.add(image)

    # import heapq
    # heap = []
    #
    # seen_images = set()
    #
    # for score, image in img_scores:
    #     if image not in seen_images:
    #         heapq.heappush(heap, (score, image))
    #         seen_images.add(image)
    #     if len(heap) > topk:
    #         _, removed_image = heapq.heappop(heap)
    #         seen_images.remove(removed_image)
    #
    # sorted_scores = sorted(heap, key=lambda x: x[0], reverse=True)
    return sorted_scores[:topk]


def compute_total_similarity(
    annos: List[Annotation],
    checked_anno: str,
    anno_refs: List[str] = None,
    max_rows: int = 50,
    show_checked_ref: bool = True,
):
    total_scores = {}
    prefix_key = "_".join(checked_anno.split("_")[:2])

    if anno_refs is None:
        anno_refs = [anno.get_ref() for anno in annos]
    for pair in doc_pairs(anno_refs):
        try:
            score_path_pair = f"{SCORES_PATH}/{'-'.join(sorted(pair))}.npy"
            if prefix_key not in score_path_pair:
                continue
            pair_scores = np.load(score_path_pair, allow_pickle=True)
        except FileNotFoundError as e:
            # TODO: trigger similarity request?
            log(f"[compute_total_similarity] no score file for {pair}", e)
            continue

        for img_name in np.unique(
            np.concatenate((pair_scores[:, 1], pair_scores[:, 2]))
        ):
            if img_name.startswith(prefix_key):
                if img_name not in total_scores:
                    total_scores[img_name] = []
                total_scores[img_name].extend(best_matches(pair_scores, img_name, pair))

    ######
    if not show_checked_ref:
        filtered_data = {
            q_img: [item for item in sim if not item[1].startswith(prefix_key)]
            for q_img, sim in total_scores.items()
        }
        total_scores = filtered_data
    #######

    # score_dict = {
    #     q_img: sorted(sim, key=lambda x: x[0], reverse=True)
    #     for q_img, sim in total_scores.items()
    # }

    ######
    score_sorted = {}
    for key, value in total_scores.items():
        if len(value):
            score_sorted[key] = value[0][0]
    score_sorted = sorted(score_sorted.items(), key=lambda x: x[1], reverse=True)

    score_dict_sorted = {}
    counter = 1
    for key, score in score_sorted:
        if counter > max_rows:
            break

        if prefix_key in key:
            score_dict_sorted[key] = get_best_matches(total_scores[key])
            # print(score_dict_sorted[key], total_scores[key][:10])
            counter += 1

    return score_dict_sorted
    #######


def best_matches(scores, q_img, doc_pair):
    """
    scores = [[score, wit1_man191_0009_166,1325,578,516.jpg,  wit205_pdf216_021_65,701,504,520.jpg]
              [score, wit1_man191_0027_1143,2063,269,245.jpg, wit205_pdf216_025_42,755,534,440.jpg]
              ...]
    q_img = "wit1_man191_0009_166,1325,578,516.jpg"
    doc_pair = (wit1_man191, wit205_pdf216)
    """
    # q_doc = "_".join(q_img.split("_")[:1])
    # q_idx, s_idx = (1, 2) if doc_pair[0].startswith(q_doc) else (2, 1)

    # Get pairs concerning the given query image q_img
    img_pairs_1 = scores[scores[:, 1] == q_img]
    img_pairs_2 = scores[scores[:, 2] == q_img]

    # [(score, similar_image)]
    result = [(float(pair[0]), pair[2]) for pair in img_pairs_1]
    result.extend([(float(pair[0]), pair[1]) for pair in img_pairs_2])

    unique_dict = {str(item): item for item in result}
    distinct_array = list(unique_dict.values())
    max_score = {}
    filtered_array = []
    for score, img in distinct_array:
        if img not in max_score or score > max_score[img]:
            max_score[img] = score
            for i, (existing_score, existing_img) in enumerate(filtered_array):
                if existing_img == img:
                    filtered_array[i] = [score, img]
                    break
            else:
                filtered_array.append([score, img])

    return filtered_array


def doc_pairs(doc_ids: list):
    if isinstance(doc_ids, list) and len(doc_ids) > 0:
        return list(combinations_with_replacement(doc_ids, 2))
    raise ValueError("Input must be a non-empty list of ids.")


def reset_similarity(anno_ref):
    # TODO function to delete all similarity files concerning the anno_ref
    # TODO send request to delete features and scores concerning the anno ref as well
    pass
