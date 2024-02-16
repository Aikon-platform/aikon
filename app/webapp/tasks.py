from typing import List

from celery import shared_task

from app.config.celery import celery_app
from app.webapp.utils.iiif.annotation import process_anno, check_indexation_annos
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


@celery_app.task
def compute_similarity_scores(anno_refs: List[str] = None):
    from app.webapp.utils.logger import log
    from app.webapp.views import check_ref

    annos = [
        anno
        for (passed, anno) in [check_ref(ref, "Annotation") for ref in anno_refs]
        if passed
    ]

    if not len(annos):
        log(f"[compute_similarity_scores] No annotation corresponding to {anno_refs}")
        return {}
    return compute_total_similarity(annos, anno_refs)


@celery_app.task
def process_anno_file(file_content, digit_id, model):
    from app.webapp.models.annotation import Digitization

    digitization = Digitization.objects.filter(pk=digit_id).first()
    return process_anno(file_content, digitization, model)


@celery_app.task
def reindex_from_file(anno_id):
    from app.webapp.models.annotation import Annotation

    annotation = Annotation.objects.filter(pk=anno_id).first()
    return check_indexation_annos(annotation, True)


@celery_app.task
def test(log_msg):
    from app.webapp.utils.logger import log

    log(log_msg or ".dlrow olleH")
