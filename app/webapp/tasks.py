from celery import shared_task

from app.config.celery import celery_app
from app.webapp.utils.iiif.annotation import process_anno, check_indexation_annos


@celery_app.task
def convert_pdf_to_imgs(pdf_path, img_path):
    # TODO: pdf_to_images_conversion
    pass


@celery_app.task
def extract_imgs_from_manifest(url, img_path, work):
    # TODO: manifest_image_extraction
    pass


@celery_app.task
def search_similarity(exp_path, work):
    # TODO: similarity_search
    pass


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
