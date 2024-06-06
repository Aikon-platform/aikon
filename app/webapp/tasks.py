from typing import List

from celery import shared_task

from app.config.celery import celery_app
from app.webapp.utils.iiif.annotation import check_indexation, process_regions
from app.webapp.utils.similarity import compute_total_similarity


@celery_app.task
def convert_pdf_to_imgs(pdf_path, img_path):
    # TODO: pdf_to_images_conversion
    pass


@celery_app.task
def extract_imgs_from_manifest(url, img_path, work):
    # TODO: manifest_image_extraction
    pass


@celery_app.task
def check_similarity_files(file_names):
    # TODO: manifest_image_extraction
    pass


# @celery_app.task
def compute_similarity_scores(
    regions_refs: List[str] = None, max_rows: int = 50, show_checked_ref: bool = False
):
    from app.webapp.views import check_ref

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
def process_regions_file(file_content, digit_id, treatment_id, model):
    from app.webapp.models.regions import Digitization

    digitization = Digitization.objects.filter(pk=digit_id).first()
    return process_regions(file_content, digitization, treatment_id, model)


@celery_app.task
def reindex_from_file(regions_id):
    from app.webapp.models.regions import Regions

    annotation = Regions.objects.filter(pk=regions_id).first()
    return check_indexation(annotation, True)


@celery_app.task
def test(log_msg):
    from app.webapp.utils.logger import log

    log(log_msg or ".dlrow olleH")
