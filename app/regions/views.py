from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

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

    manifest = {digit.get_wit_ref(): digit.gen_manifest_url()}
    error = {
        "response": f"Failed to send regions extraction request for digit #{digit.id}"
    }

    try:
        status = regions_request(manifest, "manual")
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
    TODO mutualise logic with all additional modules
    To launch regions extraction for a specific witness
    """
    from app.webapp.models.witness import Witness
    from app.webapp.models.document_set import DocumentSet
    from app.webapp.models.treatment import Treatment

    witness = Witness.objects.get(id=wit_id)
    digits = [digit for digit in witness.get_digits() if digit.has_images()]
    if not digits:
        return JsonResponse(
            {"message": f"No digitization available for witness #{wit_id}"},
            safe=False,
            status=500,
        )

    try:
        wit_str = witness.__str__()
        wit_title = wit_str if len(wit_str) < 48 else f"{wit_str[:48]}…"
        doc_set = DocumentSet.objects.create(
            title=wit_title,
            user=request.user,
            wit_ids=[wit_id],
            is_public=False,
        )
        doc_set.save()
    except Exception as e:
        log(
            f"[witness_regions_extraction] Failed to create DocumentSet for witness #{wit_id}: {e}"
        )
        return JsonResponse(
            {"message": f"Failed to create DocumentSet for witness #{wit_id}: {e}"},
            safe=False,
            status=500,
        )

    try:
        treatment = Treatment.objects.create(
            requested_by=request.user,
            task_type="regions",
            document_set=doc_set,
        )
        treatment.save()
    except Exception as e:
        log(
            f"[witness_regions_extraction] Failed to create Treatment for witness #{wit_id}",
            e,
        )
        return JsonResponse(
            {"message": f"Failed to create Treatment for witness #{wit_id}: {e}"},
            safe=False,
            status=500,
        )
    return JsonResponse(
        {"message": f"Regions extraction was launched for witness #{wit_id}"},
        safe=False,
        status=200,
    )


@user_passes_test(is_superuser)
def regions_deletion_extraction(request, digit_ref):
    """
    To delete witness digitization on the GPU and relaunch regions extraction from scratch
    """
    passed, digit = check_ref(digit_ref, "Regions")
    if not passed:
        return JsonResponse(digit)

    manifest = {digit.get_wit_ref(): digit.gen_manifest_url()}
    error = {
        "response": f"Failed to send deletion and regions extraction request for digitization #{digit.id}"
    }

    try:
        status = regions_request(manifest, "manual")
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
            # treatment_id = request.POST.get("experiment_id")
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
            process_regions_file.delay(file_content, digit.id, model)

            return JsonResponse({"response": "OK"}, status=200)

        return JsonResponse({"message": "Could not process regions file"}, status=400)
    else:
        return JsonResponse({"message": "Invalid request"}, status=400)
