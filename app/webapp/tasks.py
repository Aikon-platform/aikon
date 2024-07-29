from pathlib import Path
from typing import List

from celery import shared_task

from app.config.celery import celery_app

from app.webapp.utils.constants import MAX_RES

from app.webapp.utils.functions import pdf_to_img, temp_to_img
from app.webapp.utils.iiif.download import iiif_to_img


@celery_app.task
def convert_pdf_to_img(pdf_name, dpi=MAX_RES):
    return pdf_to_img(pdf_name, dpi=dpi)


@celery_app.task
def convert_temp_to_img(digit):
    return temp_to_img(digit)


@celery_app.task
def extract_images_from_iiif_manifest(manifest_url, digit_ref, digit):
    return iiif_to_img(manifest_url, digit_ref, digit)


@celery_app.task
def reindex_from_file(regions_id):
    from app.webapp.models.regions import Regions
    from app.webapp.utils.iiif.annotation import check_indexation

    regions = Regions.objects.filter(pk=regions_id).first()
    return check_indexation(regions, True)


@celery_app.task
def test(log_msg):
    from app.webapp.utils.logger import log

    log(log_msg or ".dlrow olleH")
