import json

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404

from app.webapp.models.digitization import Digitization
from app.webapp.models.document_set import DocumentSet
from app.webapp.models.regions import Regions
from app.webapp.models.witness import Witness
from app.webapp.utils.constants import MANIFEST_V2
from app.webapp.utils.functions import zip_img
from app.webapp.utils.iiif import gen_iiif_url
from app.webapp.utils.iiif.annotation import (
    get_regions_annotations,
)
from app.webapp.utils.logger import log
from app.webapp.utils.regions import create_empty_regions

"""
VIEWS THAT SERVE AS ENDPOINTS
ONLY FOR API CALLS
"""


@csrf_exempt
def save_document_set(request, dsid=None):
    """
    Endpoint used to create/update a document set
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))

            set_name = data.get("title")
            witness_ids = data.get("witness_ids", [])
            series_ids = data.get("series_ids", [])
            work_ids = data.get("work_ids", [])

            # TODO create logic for saving document set etc.

            if len(witness_ids) + len(series_ids) + len(work_ids) == 0:
                return JsonResponse(
                    {"error": "No documents to save in the set"}, status=400
                )

            try:
                if id:
                    document_set = DocumentSet.objects.get(id=id)
                else:
                    document_set = DocumentSet.objects.create(user=request.user)
                document_set.title = set_name
                document_set.wit_ids = witness_ids
                document_set.ser_ids = series_ids
                document_set.work_ids = work_ids
                document_set.save()

            except Exception as e:
                return JsonResponse(
                    {"error": f"Failed to save document set: {e}"}, status=500
                )
            return JsonResponse({"message": "Document set saved successfully"})
        except Exception as e:
            return JsonResponse({"message": "Error saving score files"}, status=500)
    return JsonResponse({"message": "Invalid request"}, status=400)


def get_canvas_regions(request, wid, rid):
    # TODO mutualize with get_canvas_witness_regions
    regions = get_object_or_404(Regions, id=rid)
    p_nb = int(request.GET.get("p", 0))
    if p_nb > 0:
        p_len = 50
        max_c = (
            p_nb * p_len
        )  # TODO limit to not exceed number of canvases of the witness
        min_c = max_c - p_len
        return JsonResponse(
            get_regions_annotations(
                regions, as_json=True, r_annos={}, min_c=min_c, max_c=max_c
            ),
            safe=False,
        )

    return JsonResponse(
        get_regions_annotations(regions, as_json=True),
        safe=False,
    )


def get_canvas_witness_regions(request, wid):
    witness = get_object_or_404(Witness, id=wid)
    p_nb = int(request.GET.get("p", 0))
    if p_nb > 0:
        p_len = 50
        anno_regions = {}
        max_c = (
            p_nb * p_len
        )  # TODO limit to not exceed number of canvases of the witness
        min_c = max_c - p_len
        for regions in witness.get_regions():
            anno_regions = get_regions_annotations(
                regions, as_json=True, r_annos=anno_regions, min_c=min_c, max_c=max_c
            )
    else:
        anno_regions = {}
        for regions in witness.get_regions():
            anno_regions = get_regions_annotations(
                regions, as_json=True, r_annos=anno_regions
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
