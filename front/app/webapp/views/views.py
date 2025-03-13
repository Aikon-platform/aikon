import json
import os
import requests

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from app.webapp.models.document_set import DocumentSet
from app.webapp.models.regions import Regions, check_version
from app.webapp.models.digitization import Digitization
from app.config.settings import API_URL
from app.webapp.models.treatment import Treatment
from app.webapp.utils.iiif import parse_ref
from app.webapp.utils.paths import MEDIA_DIR


def admin_app(request):
    return redirect("admin:index")


def error_404(request, exception):
    return render(
        request,
        "error.html",
        status=404,
        context={
            "error_code": 404,
            "error_title": "Page not found",
            "error_message": "The page you are looking for does not exist.",
            "exception": str(exception),
        },
    )


def error_500(request):
    return render(
        request,
        "error.html",
        status=500,
        context={
            "error_code": 500,
            "error_title": "Internal Server Error",
            "error_message": "Something went wrong. Please try again later.",
        },
    )


def error_403(request, exception):
    return render(
        request,
        "error.html",
        status=403,
        context={
            "error_code": 403,
            "error_title": "Access Denied",
            "error_message": "You do not have permission to access this page.",
        },
    )


def error_400(request, exception):
    return render(
        request,
        "error.html",
        status=400,
        context={
            "error_code": 400,
            "error_title": "Bad Request",
            "error_message": "Your request is invalid.",
        },
    )


def check_ref(obj_ref, obj="Digitization"):
    ref = parse_ref(obj_ref)
    ref_format = (
        "wit{witness_id}_{digit_abbr}{digit_id}"
        if obj == "Digitization"
        else "wit{witness_id}_{digit_abbr}{digit_id}_anno{regions_id}"
    )
    if not ref:
        return False, {
            "response": f"Wrong format of {obj} reference: {obj_ref}",
            "reason": f"Reference must follow this format: {ref_format}",
        }

    digit_id = ref["digit"][1]
    digit = Digitization.objects.filter(pk=digit_id).first()
    if not digit:
        return False, {"response": f"No digitization matching the id #{digit_id}"}

    if obj == "Digitization" or ref["regions"] is None:
        if obj_ref != digit.get_ref():
            return False, {
                "response": f"Wrong info given in reference for digitization #{digit_id}: {obj_ref} instead of {digit.get_ref()}",
                "reason": f"Reference must follow this format: {ref_format}",
            }
        return True, digit

    regions_id = ref["regions"][1]
    regions = Regions.objects.filter(pk=regions_id).first()
    if not regions:
        return False, {"response": f"No regions matching the id #{regions_id}"}

    if obj == "Regions":
        if obj_ref != regions.get_ref():
            return False, {
                "response": f"Wrong info given in reference for regions #{regions_id}",
                "reason": f"Reference must follow this format: {ref_format}",
            }
        return True, regions

    return False, {"response": f"Nothing to retrieve for {obj} #{obj_ref}"}


def manifest_digitization(request, digit_ref):
    # TODO make difference if witness is not public
    passed, digit = check_ref(digit_ref)
    if not passed:
        return JsonResponse(digit, safe=False)

    return JsonResponse(digit.gen_manifest_json())


def manifest_regions(request, version, regions_ref):
    # TODO make difference if witness is not public
    passed, regions = check_ref(regions_ref, "Regions")
    if not passed:
        return JsonResponse(regions, safe=False)

    return JsonResponse(regions.gen_manifest_json(version=check_version(version)))


# def export_digit_img(request, digit_id):
#     digit = get_object_or_404(Digitization, pk=digit_id)
#     regions = []
#     for region in digit.get_regions():
#         regions.extend(get_regions_img(region))
#     return list_to_txt(regions, digit.get_ref())


# def export_wit_img(request, wit_id):
#     wit = get_object_or_404(Witness, pk=wit_id)
#     regions = []
#     for region in wit.get_regions():
#         regions.extend(get_regions_img(region))
#     return list_to_txt(regions, wit.get_ref())


def rgpd(request):
    return render(request, "rgpd.html")


def legacy_manifest(request, old_id):
    if not os.path.isfile(f"{MEDIA_DIR}/manifest/{old_id}.json"):
        return JsonResponse({})
    with open(f"{MEDIA_DIR}/manifest/{old_id}.json", "r") as manifest:
        return JsonResponse(json.loads(manifest.read()))


@csrf_exempt
def cancel_treatment(request, treatment_id):
    """
    Cancel treatment in the API
    """
    if not treatment_id:
        return JsonResponse({"error": "Invalid treatment ID"}, status=400)
    try:
        treatment = Treatment.objects.get(id=treatment_id)

        try:
            requests.post(url=f"{API_URL}/{treatment.api_tracking_id}/cancel")
        except Exception as e:
            return JsonResponse({"error": "Could not connect to API"}, e)

        treatment.is_finished = True
        treatment.status = "CANCELLED"
        treatment.save()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": "Treatment not found"}, e)


def set_title(request, set_id):
    # TODO is it used? because it does not set anything
    try:
        doc_set = DocumentSet.objects.get(id=set_id)
        return JsonResponse({"title": doc_set.title})
    except DocumentSet.DoesNotExist:
        return JsonResponse({"title": "Unknown"}, status=404)
