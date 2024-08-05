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
def delete_regions_and_annotations(regions_id):
    from app.webapp.models.regions import Regions
    from app.webapp.utils.iiif.annotation import delete_regions

    regions = Regions.objects.filter(pk=regions_id).first()
    return delete_regions(regions)


@celery_app.task
def delete_annotations(regions_ref, manifest_url):
    from app.webapp.utils.iiif.annotation import unindex_regions

    return unindex_regions(regions_ref, manifest_url)


@celery_app.task
def get_all_witnesses(treatment):
    from app.webapp.models.witness import Witness
    from app.webapp.models.series import Series
    from app.webapp.models.work import Work

    witnesses = []

    for object in treatment.get_objects():
        if type(object) is Witness:
            try:
                witnesses.append(object)
            except:
                pass
        elif type(object) is Series or Work:
            try:
                objects = object.get_witnesses().get()
                witnesses.append(objects)
            except:
                pass
        # elif object == "digitizations":
    print(witnesses)
    treatment.start_task(witnesses)


@celery_app.task
def test(log_msg):
    from app.webapp.utils.logger import log

    log(log_msg or ".dlrow olleH")
