from celery.schedules import crontab
from celery import chain
from app.config.celery import celery_app
from django.apps import apps

from app.webapp.models.searchable_models import AbstractSearchableModel
from app.webapp.utils.constants import MAX_RES
from app.webapp.utils.iiif.download import iiif_to_img
from webapp.models.utils.constants import PDF_ABBR, IMG_ABBR, MAN_ABBR
from webapp.utils.paths import MEDIA_DIR, IMG_PATH
from webapp.utils.pdf import pdf_2_img


@celery_app.task
def convert_pdf_to_img(pdf_name, dpi=MAX_RES):
    return pdf_2_img(pdf_name, dpi=dpi)


@celery_app.task
def convert_temp_to_img(digit):
    from app.webapp.utils.functions import temp_to_img

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


@celery_app.task
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
def update_image_json(img_list, digit_id):
    """Update Witness and Digitization JSON after image post-processing"""
    if not img_list:
        return False

    try:
        from app.webapp.models.digitization import Digitization

        digit = Digitization.objects.get(id=digit_id)
        digit.update_imgs_json(img_list)

        witness = digit.witness
        witness.get_json(reindex=True)

        return True
    except Exception as e:
        return f"[update_image_json] Error updating JSON image property after processing: {e}"


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


@celery_app.task
def convert_digitization(digit_id):
    from app.webapp.models.digitization import Digitization

    try:
        instance = Digitization.objects.get(id=digit_id)
        digit_type = instance.get_digit_abbr()

        if digit_type == PDF_ABBR:
            return chain(
                convert_pdf_to_img.s(instance.get_file_path(is_abs=False)),
                update_image_json.s(instance.id),
            ).apply_async(
                countdown=1
            )  # small delay to ensure the file is saved

        elif digit_type == IMG_ABBR:
            return chain(
                convert_temp_to_img.s(instance), update_image_json.s(instance.id)
            ).apply_async(countdown=1)

        elif digit_type == MAN_ABBR:
            return chain(
                extract_images_from_iiif_manifest.s(
                    instance.manifest, instance.get_ref(), instance
                ),
                update_image_json.s(instance.id),
            ).apply_async(countdown=1)
        return f"No processing needed for digitization #{digit_id}"

    except Digitization.DoesNotExist:
        return f"Error: Digitization #{digit_id} does not exist"
    except Exception as e:
        return f"Error converting digitization {digit_id}: {e}"


@celery_app.task
def delete_digitization(digit_ref, other_media):
    from app.webapp.utils.functions import delete_files, get_files_with_prefix

    try:
        img_files = get_files_with_prefix(IMG_PATH, digit_ref, f"{IMG_PATH}/")
        delete_files(img_files)
        if other_media:
            delete_files(other_media, MEDIA_DIR)

        return f"Successfully deleted files associated to Digitization #{digit_ref}"

    except Exception as e:
        return f"Error converting digitization {digit_ref}: {e}"


@celery_app.task
def delete_regions(regions_ids):
    from app.webapp.models.regions import Regions
    from app.webapp.utils.iiif.annotation import destroy_regions

    for regions_id in regions_ids:
        try:
            regions = Regions.objects.get(id=regions_id)
            destroy_regions(regions)
        except Regions.DoesNotExist:
            return f"Error: Regions #{regions_ids} does not exist"
        except Exception as e:
            return f"Error deleting Regions {regions_ids}: {e}"
    return f"Successfully deleted regions {regions_ids}"
