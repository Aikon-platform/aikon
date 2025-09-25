import requests
from app.config.celery import celery_app
from config.settings import API_URL


@celery_app.task
def check_similarity_files(file_names):
    # TODO: manifest_image_extraction
    pass


@celery_app.task
def process_similarity_file(file):
    from app.similarity.utils import score_file_to_db

    return score_file_to_db(file)


@celery_app.task
def delete_api_similarity(regions_ref, algorithm=None, feat_net=None):
    args = {
        "algorithm": algorithm,
        "feat_net": feat_net,
    }

    response = requests.post(f"{API_URL}/similarity/{regions_ref}/delete", params=args)
    response.raise_for_status()
    return response.json()
