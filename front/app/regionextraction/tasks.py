import requests
from app.config.celery import celery_app
from config.settings import API_URL


@celery_app.task
def process_regions_file(file_content, digit_id, model):
    from app.webapp.models.regionextraction import Digitization
    from app.webapp.utils.iiif.annotation import process_regions

    digitization = Digitization.objects.filter(pk=digit_id).first()
    return process_regions(file_content, digitization, model)


@celery_app.task
def delete_api_regions(digit_ref, model_name=None):
    model = f"?model_name={model_name}" if model_name else ""
    response = requests.post(f"{API_URL}/regions/{digit_ref}/delete{model}")
    response.raise_for_status()
    return response.json()
