from collections import defaultdict

from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from app.webapp.utils.tasking import (
    receive_notification,
    create_doc_set,
)
from app.webapp.views import is_superuser, check_ref

from app.region_extraction.utils import (
    region_extraction_request,
    check_region_extraction_json_file,
)
from app.webapp.models.digitization import Digitization
from app.webapp.utils.functions import json_post
from app.webapp.utils.iiif import parse_ref
from app.webapp.utils.iiif.annotation import extend_region_extraction


@user_passes_test(is_superuser)
def send_region_extraction(request, digit_ref):
    """
    To relaunch region extraction in case the automatic extraction failed
    """
    passed, digit = check_ref(digit_ref)
    if not passed:
        return JsonResponse(digit, safe=False)

    # TODO delete regions files if existing

    error = {
        "response": f"Failed to send region extraction request for digit #{digit.id}"
    }

    try:
        status = region_extraction_request([digit.get_witness()], "manual")
    except Exception as e:
        error["cause"] = e
        return JsonResponse(error, safe=False)

    if status:
        return JsonResponse(
            {"response": f"Region extraction was relaunched for digit #{digit.id}"},
            safe=False,
        )
    return JsonResponse(error, safe=False)


@require_POST
def witness_region_extraction(request, wit_id):
    """
    To launch regions extraction for a specific witness
    """
    from app.webapp.models.witness import Witness

    witness = Witness.objects.get(id=wit_id)
    digits = [digit for digit in witness.get_digits() if digit.has_images()]
    if not digits:
        return JsonResponse(
            {"message": f"No digitization available for witness #{wit_id}"},
            safe=False,
            status=500,
        )

    try:
        doc_set, is_new = create_doc_set([witness], request.user)
    except Exception as e:
        return JsonResponse(
            {"message": f"Failed to create document set for witness #{wit_id}: {e}"},
            safe=False,
            status=500,
        )

    return JsonResponse(
        {
            "message": f"Document set was created for witness #{wit_id}",
            "doc_set_id": doc_set.id,
        },
        safe=False,
        status=200,
    )


@csrf_exempt
def receive_region_extraction_notification(request):
    """
    Receive results and notification from the API
    """
    response, status_code = receive_notification(request)
    return JsonResponse(response, status=status_code, safe=False)


@csrf_exempt
@user_passes_test(is_superuser)
@json_post
def import_regions(request, data):
    """
    Add regions to the existing ones
    {"model": "import", "regions": [{"doc_uid": digit_ref, "source": "img.jpg", "crops": [{"source": "img.jpg", "absolute": {"x1", "y1", "width", "height"}}]}]}
    """
    regions = data.get("regions", [])
    if not check_region_extraction_json_file(regions) or not all(
        "doc_uid" in page for page in regions
    ):
        raise ValueError("Invalid regions format")

    by_digit = defaultdict(list)
    for page in regions:
        by_digit[page["doc_uid"]].append(page)

    refs = []
    for doc_uid, pages in by_digit.items():
        ref = parse_ref(doc_uid)
        if not ref or not (
            digit := Digitization.objects.filter(pk=ref["digit"][1]).first()
        ):
            raise ValueError(f"Unknown digitization {doc_uid}")
        refs.append(
            extend_region_extraction(pages, digit, data.get("model") or "import")
        )
    return {"status": "success", "region_extractions": refs}
