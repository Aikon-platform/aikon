import json

from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404

from app.webapp.models.digitization import Digitization
from app.webapp.models.document_set import DocumentSet
from app.webapp.models.regions import Regions
from app.webapp.models.witness import Witness
from app.webapp.utils.constants import MANIFEST_V2, PAGE_LEN
from app.webapp.utils.functions import zip_img
from app.webapp.utils.iiif import gen_iiif_url
from app.webapp.utils.iiif.annotation import (
    get_regions_annotations,
)
from app.webapp.utils.logger import log
from app.webapp.utils.regions import create_empty_regions
from app.webapp.tasks import generate_all_json

"""
VIEWS THAT SERVE AS ENDPOINTS
ONLY FOR API CALLS
"""


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
            # TODO use title and ids retrieved from selection directly?
            set_name = data.get("title", "Document set")
            witness_ids = data.get("Witness", [])
            series_ids = data.get("Series", [])
            work_ids = data.get("Work", [])

            if len(witness_ids) + len(series_ids) + len(work_ids) == 0:
                return JsonResponse(
                    {"error": "No documents to save in the set"}, status=400
                )

            try:
                if dsid:
                    ds = DocumentSet.objects.get(id=dsid)
                else:
                    ds = DocumentSet.objects.create(user=request.user)
                ds.selection = selection
                ds.title = f"{set_name} #{ds.id}" if "#" not in set_name else set_name
                ds.wit_ids = witness_ids
                ds.ser_ids = series_ids
                ds.work_ids = work_ids
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
    regions = get_object_or_404(Regions, id=rid)
    p_nb = int(request.GET.get("p", 0))
    max_canvas = regions.get_json()["img_nb"]
    if p_nb > 0:
        p_len = PAGE_LEN
        max_c = p_nb * p_len
        min_c = max_c - p_len
        return JsonResponse(
            get_regions_annotations(
                regions,
                as_json=True,
                r_annos={},
                min_c=min_c,
                max_c=min(max_c, max_canvas),
            ),
            safe=False,
        )
    # to retrieve all regions
    return JsonResponse(
        get_regions_annotations(regions, as_json=True, min_c=1, max_c=max_canvas),
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
        for regions in witness.get_regions():
            max_canvas = regions.get_json()["img_nb"]
            anno_regions = get_regions_annotations(
                regions,
                as_json=True,
                r_annos=anno_regions,
                min_c=min_c,
                max_c=min(max_c, max_canvas),
            )
    else:
        # to retrieve all regions
        for regions in witness.get_regions():
            max_c = regions.get_json()["img_nb"]
            anno_regions = get_regions_annotations(
                regions, as_json=True, r_annos=anno_regions, min_c=1, max_c=max_c
            )

    return JsonResponse(anno_regions, safe=False)


def create_manual_regions(request, wid, did=None, rid=None):
    if request.method == "POST":
        if rid:
            regions = get_object_or_404(Regions, id=rid)
            return JsonResponse(
                {
                    "regions_id": regions.id,
                    "mirador_url": regions.gen_mirador_url(),
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

        regions = create_empty_regions(digit)
        if not regions:
            return JsonResponse({"error": "Unable to create regions"}, status=500)
        return JsonResponse(
            {
                "regions_id": regions.id,
                "mirador_url": regions.gen_mirador_url(),
            },
        )
    return JsonResponse({"error": "Invalid request method"}, status=400)


def delete_regions(request, rid):
    from app.webapp.tasks import delete_annotations

    if request.method == "DELETE":
        regions = get_object_or_404(Regions, id=rid)
        try:
            # TODO! here do not unindex the manifest because retrieve the json content after deletion
            delete_annotations.delay(
                regions.get_ref(), regions.gen_manifest_url(version=MANIFEST_V2)
            )
            try:
                # Delete the regions record in the database
                regions.delete()
            except Exception as e:
                return JsonResponse(
                    {"message": f"Failed to delete regions record #{rid}: {e}"},
                    status=400,
                )

            return JsonResponse({"message": "Regions deletion requested"}, status=204)
        except Exception as e:
            log(f"[delete_regions] Error sending deletion task for regions #{rid}", e)
            return JsonResponse(
                {"error": f" Error sending deletion task for regions #{rid}: {e}"},
                status=500,
            )
    return JsonResponse({"error": "Invalid request method"}, status=400)


def export_regions(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
        regions_ref = data.get("regionsRef")

        urls_list = []
        for ref in regions_ref:
            try:
                wit, digit, canvas, coord = ref.split("_")
                urls_list.append(
                    gen_iiif_url(f"{wit}_{digit}_{canvas}.jpg", 2, f"{coord}/full/0")
                )
            except Exception as e:
                log(f"[export_regions] Couldn't parse {ref} for export", e)

        return zip_img(urls_list)
