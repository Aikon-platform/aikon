from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse

from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt

from app.webapp.utils.logger import log
from app.webapp.utils.regions import check_regions_file
from app.webapp.views import is_superuser, check_ref

from app.regions.utils import regions_request
from app.regions.tasks import process_regions_file


@user_passes_test(is_superuser)
def send_regions_extraction(request, digit_ref):
    """
    To relaunch regions extraction in case the automatic extraction failed
    """
    passed, digit = check_ref(digit_ref)
    if not passed:
        return JsonResponse(digit, safe=False)

    error = {
        "response": f"Failed to send regions extraction request for digit #{digit.id}"
    }
    try:
        status = regions_request(
            digit, treatment_type="manual", user_id=User.objects.get(id=request.user.id)
        )
    except Exception as e:
        error["cause"] = e
        return JsonResponse(error, safe=False)

    if status:
        return JsonResponse(
            {"response": f"Regions extraction was relaunched for digit #{digit.id}"},
            safe=False,
        )
    return JsonResponse(error, safe=False)


@csrf_exempt
def receive_regions_file(request, digit_ref):
    """
    Process the result of the API containing regions extracted from a digitization
    """
    passed, digit = check_ref(digit_ref)
    if not passed:
        return JsonResponse(digit)

    if request.method == "POST":
        try:
            regions_file = request.FILES["annotation_file"]
            treatment_id = request.POST.get("experiment_id")
        except Exception as e:
            log("[receive_regions_file] No regions file received for", e)
            return JsonResponse({"message": "No regions file"}, status=400)

        try:
            model = request.POST.get("model", "Unknown model")
        except Exception as e:
            log("[receive_regions_file] Unable to retrieve model param", e)
            model = "Unknown model"
        file_content = regions_file.read()
        file_content = file_content.decode("utf-8")

        if check_regions_file(file_content):
            process_regions_file.delay(file_content, digit.id, treatment_id, model)

            return JsonResponse({"response": "OK"}, status=200)

        return JsonResponse({"message": "Could not process regions file"}, status=400)
    else:
        return JsonResponse({"message": "Invalid request"}, status=400)


@user_passes_test(is_superuser)
def regions_deletion_extraction(request, digit_ref):
    """
    To delete witness digitization on the GPU and relaunch regions extraction from scratch
    """
    passed, digit = check_ref(digit_ref, "Regions")
    if not passed:
        return JsonResponse(digit)

    error = {
        "response": f"Failed to send deletion and regions extraction request for digitization #{digit.id}"
    }

    try:
        status = regions_request(
            digit, treatment_type="manual", user_id=request.user.id
        )
    except Exception as e:
        error["cause"] = e
        return JsonResponse(error, safe=False)

    if status:
        return JsonResponse(
            {"response": f"Regions extraction was relaunched for digit #{digit.id}"},
            safe=False,
        )
    return JsonResponse(error, safe=False)
