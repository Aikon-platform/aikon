import json

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404

from app.webapp.models.digitization import Digitization
from app.webapp.models.regions import Regions
from app.webapp.models.witness import Witness
from app.webapp.utils.iiif.annotation import get_regions_annotations
from app.webapp.utils.regions import create_empty_regions

"""
VIEWS THAT SERVE AS ENDPOINTS
ONLY FOR API CALLS
"""


@csrf_exempt
def save_document_set(request):
    """
    Endpoint used to create/update a document set
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))

            witness_ids = data.get("witness_ids", [])
            series_ids = data.get("series_ids", [])
            regions_ids = data.get("regions_ids", [])

            # TODO create logic for saving document set etc.

            if len(witness_ids) + len(series_ids) + len(regions_ids) == 0:
                return JsonResponse(
                    {"error": "No documents to save in the set"}, status=400
                )
            return JsonResponse({"message": "Document set saved successfully"})
        except Exception as e:
            return JsonResponse({"message": "Error saving score files"}, status=500)
    return JsonResponse({"message": "Invalid request"}, status=400)


def get_canvas_regions(request, wid, rid):
    regions = get_object_or_404(Regions, id=rid)
    p_nb = int(request.GET.get("p", 1))
    p_len = 50
    anno_regions = {}
    max_c = p_nb * p_len  # TODO limit to not exceed number of canvases of the witness
    min_c = max_c - p_len

    return JsonResponse(
        get_regions_annotations(
            regions, as_json=True, r_annos=anno_regions, min_c=min_c, max_c=max_c
        ),
        safe=False,
    )


def get_canvas_witness_regions(request, wid):
    witness = get_object_or_404(Witness, id=wid)
    p_nb = int(request.GET.get("p", 1))
    p_len = 50
    anno_regions = {}
    max_c = p_nb * p_len  # TODO limit to not exceed number of canvases of the witness
    min_c = max_c - p_len
    for regions in witness.get_regions():
        anno_regions = get_regions_annotations(
            regions, as_json=True, r_annos=anno_regions, min_c=min_c, max_c=max_c
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
                status=204,
            )

        witness = get_object_or_404(Witness, id=wid)
        if did:
            digit = get_object_or_404(Digitization, id=did)
        else:
            digit = witness.get_digits()
            # todo check if has images

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
            status=204,
        )
    return JsonResponse({"error": "Invalid request"}, status=400)
