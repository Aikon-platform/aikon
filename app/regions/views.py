from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from app.webapp.utils.logger import log
from app.webapp.utils.tasking import create_treatment, receive_notification
from app.webapp.views import is_superuser, check_ref

from app.regions.utils import regions_request


@user_passes_test(is_superuser)
def send_regions_extraction(request, digit_ref):
    """
    To relaunch regions extraction in case the automatic extraction failed
    """
    passed, digit = check_ref(digit_ref)
    if not passed:
        return JsonResponse(digit, safe=False)

    # TODO delete regions files if existing

    error = {
        "response": f"Failed to send regions extraction request for digit #{digit.id}"
    }

    try:
        status = regions_request([digit.get_witness()], "manual")
    except Exception as e:
        error["cause"] = e
        return JsonResponse(error, safe=False)

    if status:
        return JsonResponse(
            {"response": f"Regions extraction was relaunched for digit #{digit.id}"},
            safe=False,
        )
    return JsonResponse(error, safe=False)


@require_POST
def witness_regions_extraction(request, wit_id):
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
        create_treatment([witness], "regions", request.user)
    except Exception as e:
        return JsonResponse(
            {
                "message": f"Failed to launch region extraction for witness #{wit_id}: {e}"
            },
            safe=False,
            status=500,
        )

    return JsonResponse(
        {"message": f"Regions extraction was launched for witness #{wit_id}"},
        safe=False,
        status=200,
    )


@csrf_exempt
def receive_regions_notification(request, digit_ref):
    """
    Receive results and notification from the API
    """
    response, status_code = receive_notification(request)
    return JsonResponse(response, status=status_code, safe=False)
