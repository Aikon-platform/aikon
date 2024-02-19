import hashlib
import os
from itertools import combinations_with_replacement
import numpy as np

import requests
from typing import List

from app.config.settings import EXAPI_URL, EXAPI_KEY, APP_URL, APP_NAME
from app.webapp.models.annotation import Annotation
from app.webapp.utils.functions import flatten_dict
from app.webapp.utils.iiif import gen_iiif_url
from app.webapp.utils.iiif.annotation import formatted_annotations
from app.webapp.utils.logger import log
from app.webapp.utils.paths import SCORES_PATH


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
            url=f"{EXAPI_URL}/run_detect",
            headers={"X-API-Key": EXAPI_KEY},
            json={
                "document": documents,
                # "model": f"{FEAT_BACKBONE}",
                "callback": f"{APP_URL}/{APP_NAME}/similarity",
            },
        )
        if response.status_code == 200:
            return True
        else:
            log(
                f"[similarity_request] Request failed for {list(documents.keys())} with status code: {response.status_code}"
            )
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


def compute_total_similarity(annos: List[Annotation], anno_refs: List[str] = None):
    total_scores = {}
    if anno_refs is None:
        anno_refs = [anno.get_ref() for anno in annos]

    for pair in doc_pairs(anno_refs):
        try:
            # previous naming convention hash_pair(pair)
            pair_scores = np.load(
                f"{SCORES_PATH}/{'-'.join(sorted(pair))}.npy", allow_pickle=True
            )
        except FileNotFoundError as e:
            # TODO: trigger similarity request?
            log(f"[compute_total_similarity] no score file for {pair}", e)
            continue

        # for img_name, img_url in [get_annotation_urls(anno).items() for anno in annos]:
        for img_name in np.unique(
            np.concatenate((pair_scores[:, 1], pair_scores[:, 2]))
        ):
            if img_name not in total_scores:
                total_scores[img_name] = []
            total_scores[img_name].extend(best_matches(pair_scores, img_name, pair))
            # total_scores[img_name].extend(
            #     best_matches(pair_scores, f"{img_name}.jpg", pair)
            # )

    return {
        q_img: sorted(sim, key=lambda x: x[0], reverse=True)
        for q_img, sim in total_scores.items()
    }


def best_matches(scores, q_img, doc_pair):
    """
    scores = [[score, wit1_man191_0009_166,1325,578,516.jpg,  wit205_pdf216_021_65,701,504,520.jpg]
              [score, wit1_man191_0027_1143,2063,269,245.jpg, wit205_pdf216_025_42,755,534,440.jpg]
              ...]
    q_img = "wit1_man191_0009_166,1325,578,516.jpg"
    doc_pair = (wit1_man191, wit205_pdf216)
    """
    q_doc = "_".join(q_img.split("_")[:1])
    q_idx, s_idx = (1, 2) if q_doc == doc_pair[0] else (2, 1)

    # Get pairs concerning the given query image q_img
    img_pairs = scores[scores[:, q_idx] == q_img]

    # [(score, similar_image)]
    return [(float(pair[0]), pair[s_idx]) for pair in img_pairs]


def hash_str(string):
    hash_object = hashlib.sha256()
    hash_object.update(string.encode("utf-8"))
    return hash_object.hexdigest()


def hash_pair(pair: tuple):
    if (
        isinstance(pair, tuple)
        and len(pair) == 2
        and all(isinstance(s, str) for s in pair)
    ):
        return hash_str("".join(sorted(pair)))
    raise ValueError("Not a correct pair of document id")


def doc_pairs(doc_ids: list):
    if isinstance(doc_ids, list) and len(doc_ids) > 0:
        return list(combinations_with_replacement(doc_ids, 2))
    raise ValueError("Input must be a non-empty list of ids.")
