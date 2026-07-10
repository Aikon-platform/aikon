from celery.schedules import crontab
from celery import chain, chord
from app.config.celery import celery_app
from django.apps import apps

from app.webapp.models.searchable_models import AbstractSearchableModel
from app.webapp.utils.constants import MAX_RES
from app.webapp.utils.iiif.download import iiif_to_img
from webapp.models.utils.constants import PDF_ABBR, IMG_ABBR, MAN_ABBR
from webapp.utils.paths import MEDIA_PATH, IMG_PATH
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
def reindex_from_file(region_extraction_id):
    from app.webapp.models.region_extraction import RegionExtraction
    from app.webapp.utils.iiif.annotation import check_indexation

    # region_extraction = RegionExtraction.objects.filter(pk=region_extraction_id).first()
    region_extraction = RegionExtraction.objects.get(pk=region_extraction_id)
    return check_indexation(region_extraction, True)


# NOTE unused
@celery_app.task
def delete_region_extraction_and_annotations(regions_id):
    from app.webapp.models.region_extraction import RegionExtraction
    from app.webapp.utils.iiif.annotation import destroy_region_extraction

    # region_extraction = RegionExtraction.objects.filter(pk=regions_id).first()
    region_extraction = RegionExtraction.objects.get(pk=regions_id)
    return destroy_region_extraction(region_extraction)


@celery_app.task
def delete_annotations(regions_ref, manifest_url):
    from app.webapp.utils.iiif.annotation import unindex_region_extraction

    return unindex_region_extraction(regions_ref, manifest_url)


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
    if treatment.task_type == "import":
        return start_import(str(treatment.id))
    try:
        witnesses = treatment.get_witnesses()
        treatment.start_task(witnesses)
    except Exception as e:
        from app.webapp.utils.logger import log

        log("Error when starting the task", e)
        treatment.on_task_error(
            {
                "error": f"Error when starting the task: {e}",
                "notify": treatment.notify_email,
            },
        )


@celery_app.task
def start_import(treatment_id):
    """
    Orchestrator for cross-instance imports:
    - fetch source, import witnesses + metadata cascade synchronously
    - launch one chain per digitization (download imgs → update json → import regions)
    - a chord callback finalizes the treatment (and imports similarities)
    """
    from app.webapp.models.treatment import Treatment
    from app.webapp.utils.data_import import (
        ImportContext, is_same_instance, resolve_source, import_witness,
    )
    from app.webapp.utils.tasking import create_doc_set_from_ids
    from app.webapp.utils.logger import log

    treatment = Treatment.objects.get(pk=treatment_id)
    ctx = ImportContext(treatment)
    source_url = ctx.opts.get("source_url", "")

    if is_same_instance(source_url):
        treatment.on_task_success(
            {"notify": treatment.notify_email, "message": "Source is this instance, nothing to import"}
        )
        return

    try:
        wit_urls, similarity_url = resolve_source(source_url, ctx)
        ctx.opts["similarity_url"] = similarity_url
    except Exception as e:
        treatment.on_task_error(
            {"notify": treatment.notify_email, "error": f"Could not fetch source {source_url}: {e}"}
        )
        return

    chains = []
    for wit_url in wit_urls.values():
        try:
            witness, digits = import_witness(wit_url, ctx)
        except Exception as e:
            ctx.errors.append(f"{wit_url}: {e}")
            log(f"[start_import] Failed to import witness {wit_url}", e)
            continue
        for digit, manifest_url, regions in digits:
            sig = chain(
                extract_images_from_iiif_manifest.s(manifest_url, digit.get_ref(), digit),
                update_image_json.s(digit.id),
            )
            if regions and ctx.opts.get("import_regions"):
                sig |= import_regions_task.s(digit.id, regions, treatment_id)
            chains.append(sig)

    if wit_ids := sorted(ctx.mapping["witnesses"].values()):
        doc_set, _ = create_doc_set_from_ids({"wit_ids": wit_ids}, user=treatment.requested_by)
        treatment.update(document_set=doc_set)
    ctx.save()

    if chains:
        chord(chains)(finalize_import.s(treatment_id).on_error(import_failed.s(treatment_id)))
    else:
        finalize_import.delay(None, treatment_id)


@celery_app.task
def import_regions_task(img_list, digit_id, regions, treatment_id):
    """
    Chained after update_image_json.
    regions: {src_regions_id: extracted-regions url}
    """
    from app.webapp.models.digitization import Digitization
    from app.webapp.utils.data_import import import_region_extraction, update_mapping
    from app.webapp.utils.logger import log

    digit = Digitization.objects.get(id=digit_id)
    if not digit.img_nb():
        return f"No images for digit #{digit_id}, skipping regions import"

    for src_rid, url in regions.items():
        try:
            if new_rid := import_region_extraction(digit, url):
                update_mapping(treatment_id, "regions", src_rid, new_rid)
        except Exception as e:
            log(f"[import_regions_task] Failed to import regions {url} for digit #{digit_id}", e)
    return True


@celery_app.task
def import_failed(request, exc, traceback, treatment_id):
    from app.webapp.models.treatment import Treatment

    treatment = Treatment.objects.get(pk=treatment_id)
    treatment.on_task_error(
        {"notify": treatment.notify_email, "error": f"Import chain failed: {exc}"}
    )


@celery_app.task
def finalize_import(results, treatment_id):
    from app.config.settings import ADDITIONAL_MODULES
    from app.webapp.models.treatment import Treatment
    from app.webapp.utils.data_import import ImportContext, import_similarity_pairs
    from app.webapp.utils.logger import log

    treatment = Treatment.objects.get(pk=treatment_id)
    ctx = ImportContext(treatment)
    msg = f"Imported {len(ctx.mapping['witnesses'])} witness(es)"

    sim_url = ctx.opts.get("similarity_url")
    if ctx.opts.get("import_similarities") and sim_url and "similarity" in ADDITIONAL_MODULES:
        try:
            msg += f", {import_similarity_pairs(ctx, sim_url)} region pair(s)"
        except Exception as e:
            ctx.errors.append(f"similarity: {e}")
            log("[finalize_import] Failed to import similarity pairs", e)

    ctx.save()
    if ctx.errors:
        treatment.on_task_error({"notify": treatment.notify_email, "error": f"{msg}. Errors: {ctx.errors}"})
    else:
        treatment.on_task_success({"notify": treatment.notify_email, "message": msg})


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
        # bypass saving logic
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
        # reindex to add first image to witness metadata
        witness.get_json(reindex=True)

        return True
    except Exception as e:
        return f"[update_image_json] Error updating JSON image property after processing: {e}"


@celery_app.task
def regenerate_witness_json(witness_id):
    from app.webapp.models.witness import Witness

    witness = Witness.objects.get(id=witness_id)
    digits = witness.get_digits()
    for digit in digits:
        digit.update_imgs_json(force=True)
        digit.update_json(digit.to_json(no_img=True))

    witness.get_json(reindex=True)
    return f"[regenerate_witness_json] Regenerated witness #{witness_id} and {len(digits)} digitization(s)"


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
            delete_files(other_media, MEDIA_PATH)

        return f"Successfully deleted files associated to Digitization #{digit_ref}"

    except Exception as e:
        return f"Error converting digitization {digit_ref}: {e}"


@celery_app.task
def delete_region_extraction(regions_ids):
    from app.webapp.models.region_extraction import RegionExtraction
    from app.webapp.utils.iiif.annotation import destroy_region_extraction

    for regions_id in regions_ids:
        try:
            regions = RegionExtraction.objects.get(id=regions_id)
            destroy_region_extraction(regions)
        except RegionExtraction.DoesNotExist:
            return f"Error: RegionExtraction #{regions_ids} does not exist"
        except Exception as e:
            return f"Error deleting RegionExtraction {regions_ids}: {e}"
    return f"Successfully deleted region extraction {regions_ids}"
