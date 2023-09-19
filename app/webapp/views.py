import json
import requests
from dal import autocomplete
import threading
from os.path import exists

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.decorators import login_required
from iiif_prezi.factory import StructuralError

from app.webapp.models import get_wit_abbr
from app.webapp.models.digitization import Digitization
from app.webapp.models.witness import Witness
from app.webapp.models.utils.constants import MS, VOL
from app.config.settings import (
    APP_URL,
    SAS_APP_URL,
    APP_NAME,
    ENV,
    GEONAMES_USER,
    API_GPU_URL,
)
from app.webapp.utils.constants import MANIFEST_V1
from app.webapp.utils.functions import credentials, list_to_txt
from app.webapp.utils.logger import console, log, get_time
from app.webapp.utils.iiif.annotation import (
    format_canvas_annos,
    index_annotations,
    get_anno_img,
    formatted_digit_anno,
    # index_anno,
    get_canvas_list,
    get_indexed_canvas_annos,
    check_anno_file,
    check_indexation_annos,
    anno_request,
    process_anno,
)
import requests

from app.webapp.utils.paths import BASE_DIR, ANNO_PATH


def admin_app(request):
    return redirect("admin:index")


def manifest_digitization(request, digit_id):
    digit = get_object_or_404(Digitization, pk=digit_id)
    return JsonResponse(digit.get_manifest_json())


# def manifest_manuscript(request, wit_id, version):
#     """
#     Build a manuscript manifest using iiif-prezi library IIIF Presentation API 2.0
#     """
#     return JsonResponse(manifest_wit_type(wit_id, MS, version))
#
#
# def manifest_volume(request, wit_id, version):
#     """
#     Build a volume manifest using iiif-prezi library IIIF Presentation API 2.0
#     """
#     return JsonResponse(manifest_wit_type(wit_id, VOL, version))


def send_anno(request, digit_id):
    """
    To relaunch annotations in case the automatic annotation failed
    """
    digit = get_object_or_404(Digitization, pk=digit_id)
    error = {"response": f"Failed to send annotation request for digit #{digit_id}"}
    try:
        status = anno_request(digit)
    except Exception as e:
        error["cause"] = e
        return JsonResponse(error, safe=False)

    if status:
        return JsonResponse(
            {"response": f"Annotations were relaunched for digit #{digit_id}"},
            safe=False,
        )
    return JsonResponse(error, safe=False)


@csrf_exempt
def receive_anno(request, digit_id):
    digit = get_object_or_404(Digitization, pk=digit_id)
    if request.method == "POST":
        annotation_file = request.FILES["annotation_file"]
        file_content = annotation_file.read()

        if process_anno(file_content, digit):
            return JsonResponse({"response": "OK"}, status=200)
    else:
        return JsonResponse({"message": "Invalid request"}, status=400)


def export_anno_img(request, wit_id, wit_type):
    annotations = get_anno_img(anno)
    return list_to_txt(annotations, anno.get_ref)


def canvas_annotations(request, wit_id, version, wit_type, canvas):
    return JsonResponse(format_canvas_annos(anno, canvas))


def populate_annotation(request, wit_id, wit_type):
    """
    Populate annotation store from IIIF Annotation List
    """
    if not ENV("DEBUG"):
        credentials(f"{SAS_APP_URL}/", ENV("SAS_USERNAME"), ENV("SAS_PASSWORD"))

    return HttpResponse(status=200 if index_annotations(wit_id, wit_type) else 500)


def validate_annotation(request, wit_id, wit_type):
    """
    Validate the manually corrected annotations
    """
    try:
        witness = get_object_or_404(Witness, pk=wit_id)
        witness.manifest_final = True
        witness.save()
        return HttpResponse(status=200)
    # except (Witness.DoesNotExist):
    #     return HttpResponse(f"{wit_type} #{wit_id} does not exist", status=500)
    except Exception as e:
        return HttpResponse(f"An error occurred: {e}", status=500)


def witness_sas_annotations(request, wit_id, wit_type):
    witness = get_object_or_404(Witness, pk=wit_id)
    _, canvas_annos = formatted_digit_anno(digit)
    return JsonResponse(canvas_annos, safe=False)


def test(request, wit_id, wit_type):
    start = get_time()
    model = Annotation
    try:
        wit_id = int(wit_id)
        if int(wit_id) == 0:
            annos = model.objects.all()
        else:
            annos = [get_object_or_404(model, pk=anno_id)]
    except ValueError as e:
        console(f"[test] wit_id is not an integer: {e}")
        return JsonResponse(
            {"response": f"wit_id is not an integer: {wit_id}\n{e}"},
            safe=False,
        )

    threads = []
    wit_ids = []
    # for witness in witnesses:
    #     if not witness.manifest_final:
    #         wit_ids.append(witness.id)
    #         thread = threading.Thread(
    #             target=check_indexation_annos, args=(digit, True)
    #         )
    #         thread.start()
    #         threads.append(thread)

    return JsonResponse(
        {"response": f"Execution time: {start} > {get_time()}", "checked ids": wit_ids},
        safe=False,
    )


@login_required(login_url=f"/{APP_NAME}-admin/")
def show_witness(request, wit_id, wit_type):
    witness = get_object_or_404(Witness, pk=wit_id)

    if not ENV("DEBUG"):
        credentials(f"{SAS_APP_URL}/", ENV("SAS_USERNAME"), ENV("SAS_PASSWORD"))

    bboxes, canvas_annos = formatted_digit_anno(digit)

    paginator = Paginator(canvas_annos, 50)
    try:
        page_annos = paginator.page(request.GET.get("page"))
    except PageNotAnInteger:
        page_annos = paginator.page(1)
    except EmptyPage:
        page_annos = paginator.page(paginator.num_pages)

    return render(
        request,
        "webapp/show.html",
        context={
            "wit_type": wit_type,
            "wit_obj": witness,
            "page_annos": page_annos,
            "bboxes": json.dumps(bboxes),
            "url_manifest": f"{APP_URL}/{APP_NAME}/iiif/v2/{wit_type}/{wit_id}/manifest.json",
        },
    )


class PlaceAutocomplete(autocomplete.Select2ListView):
    def get_list(self):
        query = self.request.GET.get("q", "")
        url = f"http://api.geonames.org/searchJSON?q={query}&maxRows=10&username={GEONAMES_USER}"
        response = requests.get(url)
        data = response.json()
        suggestions = []
        for suggestion in data["geonames"]:
            suggestions.append(suggestion["name"])

        return suggestions


# TODO: create test to find integrity of a manuscript:
#  if it has the correct number of images, if all its images are img files
#  if annotations were correctly defined (same img name in file that images on server)
