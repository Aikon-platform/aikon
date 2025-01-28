from typing import List

from app.config.celery import celery_app


@celery_app.task
def check_similarity_files(file_names):
    # TODO: manifest_image_extraction
    pass


@celery_app.task
def process_similarity_file(pair):
    from app.similarity.utils import score_file_to_db

    return score_file_to_db(pair)
