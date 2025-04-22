from celery.schedules import crontab
from app.config.celery import celery_app
from django.apps import apps

from app.webapp.models.searchable_models import AbstractSearchableModel
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
    from app.webapp.utils.iiif.annotation import destroy_regions

    regions = Regions.objects.filter(pk=regions_id).first()
    return destroy_regions(regions)


@celery_app.task
def delete_annotations(regions_ref, manifest_url):
    from app.webapp.utils.iiif.annotation import unindex_regions

    return unindex_regions(regions_ref, manifest_url)


@celery_app.task
def generate_all_json():
    total_updated = 0
    errors = []
    models = []
    for model in apps.get_models():
        if (
            issubclass(model, AbstractSearchableModel)
            and model != AbstractSearchableModel
        ):
            try:
                model.regenerate_all_json()
                total_updated += model.objects.count()
                models.append(model.__name__)
            except Exception as e:
                import traceback

                errors.append(f"Error updating {model.__name__}: {e}")
                traceback.print_exc()

    result = f"Updated JSON for {total_updated} objects in models: {', '.join(models)}"
    if errors:
        result += f"\nErrors encountered: {', '.join(errors)}"
    return result


@celery_app.task
def launch_task(treatment):
    try:
        witnesses = treatment.get_witnesses()
        treatment.start_task(witnesses)
    except Exception as e:
        treatment.on_task_error(
            {
                "error": f"Error when retrieving documents from set: {e}",
                "notify": treatment.notify_email,
            },
        )


def generate_record_json(model_name, record_id):
    """
    Generate JSON for a searchable record.
    """
    from app.webapp.utils.logger import log

    model_class = apps.get_model("webapp", model_name)
    try:
        instance = model_class.objects.get(pk=record_id)
        json_data = instance.to_json()
        model_class.objects.filter(pk=record_id).update(json=json_data)
    except Exception as e:
        log(
            f"[generate_record_json] Error on json generation for {model_name} #{record_id}",
            e,
        )


@celery_app.task
def test(log_msg):
    from app.webapp.utils.logger import log

    log(log_msg or ".dlrow olleH")


@celery_app.on_after_configure.connect
def periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(hour=str(3), minute=str(0)),  # Run every day at 3:00 AM
        generate_all_json.s(),
    )
