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
def check_similarity_files(file_names):
    # TODO: manifest_image_extraction
    pass


# @celery_app.task
def compute_similarity_scores(
    regions_refs: List[str] = None, max_rows: int = 50, show_checked_ref: bool = False
):
    from app.webapp.views import check_ref
    from app.webapp.utils.similarity import compute_total_similarity

    checked_regions = regions_refs[0]

    regions = [
        region
        for (passed, region) in [check_ref(ref, "Regions") for ref in regions_refs]
        if passed
    ]

    if not len(regions):
        from app.webapp.utils.logger import log

        log(
            f"[compute_similarity_scores] No annotation corresponding to {regions_refs}"
        )
        return {}
    return compute_total_similarity(
        regions, checked_regions, regions_refs, max_rows, show_checked_ref
    )


@celery_app.task
def reindex_from_file(regions_id):
    from app.webapp.models.regions import Regions
    from app.webapp.utils.iiif.annotation import check_indexation

    regions = Regions.objects.filter(pk=regions_id).first()
    return check_indexation(regions, True)


@celery_app.task
def delete_regions_and_annotations(regions_id):
    from app.webapp.models.regions import Regions
    from app.webapp.utils.iiif.annotation import delete_regions

    regions = Regions.objects.filter(pk=regions_id).first()
    return delete_regions(regions)


@celery_app.task
def test(log_msg):
    from app.webapp.utils.logger import log

    log(log_msg or ".dlrow olleH")
