from celery import shared_task

from app.config.celery import celery_app


@celery_app.task
def process_regions_file(file_content, digit_id, model):
    from app.webapp.models.regions import Digitization
    from app.webapp.utils.iiif.annotation import process_regions

    digitization = Digitization.objects.filter(pk=digit_id).first()
    return process_regions(file_content, digitization, model)
