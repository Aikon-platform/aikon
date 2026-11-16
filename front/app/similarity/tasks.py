from pathlib import Path

import requests
from app.config.celery import celery_app
from app.config.settings import API_URL


@celery_app.task
def check_similarity_files(file_names):
    # TODO: manifest_image_extraction
    pass


@celery_app.task
def process_similarity_file(file):
    from app.similarity.utils import score_file_to_db

    return score_file_to_db(file)


@celery_app.task
def download_similarity_file(url: str, path: str, replace=False, clean=False):
    from app.similarity.utils import download_scores, score_file_to_db

    if download_scores(url, Path(path), replace):
        score_file_to_db(path, clean)


@celery_app.task
def rescore_similarity_pairs(url: str, param_hash: str):
    from app.similarity.utils import json_to_scores_tuples, rescore_to_db

    response = requests.get(url, timeout=(10, 300))
    response.raise_for_status()
    rescore_to_db(json_to_scores_tuples(response.json()), param_hash)


@celery_app.task
def delete_api_similarity(ref, algorithm=None, feat_net=None):
    """
    ref can be region_extraction_ref or witness_id
    """
    args = {
        "algorithm": algorithm,
        "feat_net": feat_net,
    }

    response = requests.post(f"{API_URL}/similarity/{ref}/delete", params=args)
    response.raise_for_status()
    return response.json()
