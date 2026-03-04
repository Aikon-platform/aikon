import json
from pathlib import Path

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import cache_page

from app.webapp.models.digitization import Digitization
from app.webapp.models.document_set import DocumentSet
from app.webapp.models.region_extraction import RegionExtraction
from app.webapp.models.witness import Witness
from app.webapp.utils.constants import MANIFEST_V2, PAGE_LEN

from app.webapp.utils.iiif.annotation import (
    get_regions_annotations,
)
from app.webapp.utils.logger import log
from app.webapp.utils.paths import MEDIA_PATH
from app.webapp.utils.region_extraction import create_empty_region_extraction
from app.webapp.tasks import generate_all_json
from webapp.utils.paths import REGIONS_PATH
from webapp.utils.tasking import create_doc_set

# TODO ORGANISE THESE VIEWS BETTER


def json_regeneration(request):
    task = generate_all_json.delay()
    return JsonResponse(
        {"message": "JSON regeneration task started", "task_id": str(task.id)}
    )


def save_document_set(request, dsid=None):
    """
    Endpoint used to create/update a document set
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))

            selection = data.get("selection", [])
            set_name = data.get("title", None)
            witness_ids = data.get("Witness", [])
            series_ids = data.get("Series", [])
            work_ids = data.get("Work", [])
            shared_with = data.get("User", [])
            is_public = data.get("is_public", False)

            if len(witness_ids) + len(series_ids) + len(work_ids) == 0:
                return JsonResponse(
                    {"error": "No documents to save in the set"}, status=400
                )

            try:
                keep_title = False
                if dsid:
                    ds = DocumentSet.objects.get(id=dsid)
                    ds.wit_ids = witness_ids
                    ds.ser_ids = series_ids
                    ds.work_ids = work_ids
                    ds.shared_with = shared_with
                    ds.is_public = is_public
                else:
                    ds, is_new = create_doc_set(
                        {
                            "wit_ids": witness_ids,
                            "ser_ids": series_ids,
                            "work_ids": work_ids,
                        },
                        user=request.user,
                        shared_with=shared_with,
                        is_public=is_public,
                    )
                    keep_title = not is_new

                ds.selection = selection
                title = ds.title if keep_title else set_name
                ds.title = f"{title} #{ds.id}" if "#" not in title else title

                ds.save()

            except Exception as e:
                return JsonResponse(
                    {"error": f"Failed to save document set: {e}"}, status=500
                )
            return JsonResponse(
                {
                    "message": "Document set saved successfully",
                    "document_set_id": ds.id,
                    "document_set_title": ds.title,
                }
            )
        except Exception as e:
            return JsonResponse(
                {"message": f"Error saving score files: {e}"}, status=500
            )
    return JsonResponse({"message": "Invalid request"}, status=400)


def get_canvas_regions(request, wid, rid):
    # TODO mutualize with get_canvas_witness_regions
    region_extraction = get_object_or_404(RegionExtraction, id=rid)
    p_nb = int(request.GET.get("p", 0))
    max_canvas = region_extraction.get_json()["img_nb"]
    if p_nb > 0:
        p_len = PAGE_LEN
        max_c = p_nb * p_len
        min_c = max_c - p_len
        return JsonResponse(
            get_regions_annotations(
                region_extraction,
                as_json=True,
                r_annos={},
                min_c=min_c,
                max_c=min(max_c, max_canvas),
            ),
            safe=False,
        )
    # to retrieve all regions
    return JsonResponse(
        get_regions_annotations(
            region_extraction, as_json=True, min_c=1, max_c=max_canvas
        ),
        safe=False,
    )


def get_canvas_witness_regions(request, wid):
    witness = get_object_or_404(Witness, id=wid)
    p_nb = int(request.GET.get("p", 0))
    anno_regions = {}
    if p_nb > 0:
        p_len = PAGE_LEN
        max_c = p_nb * p_len
        min_c = max_c - p_len
        for region_extraction in witness.get_region_extractions():
            max_canvas = region_extraction.get_json()["img_nb"]
            anno_regions = get_regions_annotations(
                region_extraction,
                as_json=True,
                r_annos=anno_regions,
                min_c=min_c,
                max_c=min(max_c, max_canvas),
            )
    else:
        # to retrieve all regions
        for region_extraction in witness.get_region_extractions():
            max_c = region_extraction.get_json()["img_nb"]
            anno_regions = get_regions_annotations(
                region_extraction,
                as_json=True,
                r_annos=anno_regions,
                min_c=1,
                max_c=max_c,
            )

    return JsonResponse(anno_regions, safe=False)


def create_manual_region_extraction(request, wid, did=None, rid=None):
    if request.method == "POST":
        if rid:
            region_extraction = get_object_or_404(RegionExtraction, id=rid)
            return JsonResponse(
                {
                    "region_extraction_id": region_extraction.id,
                    "mirador_url": region_extraction.gen_mirador_url(),
                },
            )

        witness = get_object_or_404(Witness, id=wid)
        digit = None
        if did:
            digit = get_object_or_404(Digitization, id=did)
        else:
            for d in witness.get_digits():
                if d.has_images():
                    digit = d
                    break

        if not digit:
            return JsonResponse(
                {"error": "No digitization available for this witness"}, status=500
            )

        region_extraction = create_empty_region_extraction(digit)
        if not region_extraction:
            return JsonResponse(
                {"error": "Unable to create region extraction"}, status=500
            )
        return JsonResponse(
            {
                "region_extraction_id": region_extraction.id,
                "mirador_url": region_extraction.gen_mirador_url(),
            },
        )
    return JsonResponse({"error": "Invalid request method"}, status=400)


def delete_region_extraction(request, rid):
    from app.webapp.tasks import delete_annotations
    from app.region_extraction.tasks import delete_api_region_extraction

    if request.method != "DELETE":
        return JsonResponse({"error": "Invalid request method"}, status=400)
    region_extraction = get_object_or_404(RegionExtraction, id=rid)
    try:
        delete_annotations.delay(
            region_extraction.get_ref(),
            region_extraction.gen_manifest_url(version=MANIFEST_V2),
        )

        Path(f"{REGIONS_PATH}/{region_extraction.get_ref()}.json").unlink(
            missing_ok=True
        )

        delete_api_region_extraction.delay(
            region_extraction.get_digit().get_ref(), region_extraction.model
        )

        try:
            # Delete the region extraction record in the database
            region_extraction.delete()
        except Exception as e:
            return JsonResponse(
                {"message": f"Failed to delete region extraction record #{rid}: {e}"},
                status=400,
            )

        return JsonResponse(
            {"message": "RegionExtraction deletion requested"}, status=204
        )
    except Exception as e:
        log(
            f"[delete_region_extraction] Error sending deletion task for region extraction #{rid}",
            e,
        )
        return JsonResponse(
            {
                "error": f" Error sending deletion task for region extraction #{rid}: {e}"
            },
            status=500,
        )


# DIRTY FIX FOR SAS 😡
@cache_page(60 * 60 * 24)  # Cache for 24h
def iiif_context(request):
    try:
        context_path = MEDIA_PATH / "context.json"
        if not context_path.exists():
            import requests

            response = requests.get("http://iiif.io/api/presentation/2/context.json")
            context_data = response.json()
            with open(context_path, "w") as f:
                json.dump(context_data, f)
        else:
            with open(context_path, "r") as f:
                context_data = json.load(f)

        return JsonResponse(
            context_data,
            content_type="application/json",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            },
        )

    except Exception as e:
        return JsonResponse({"error": f"Unable to load IIIF context: {e}"}, status=500)
