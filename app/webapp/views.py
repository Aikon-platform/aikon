import json
import re

from dal import autocomplete

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.decorators import login_required

from app.webapp.models.annotation import Annotation, check_version
from app.webapp.models.digitization import Digitization
from app.config.settings import (
    SAS_APP_URL,
    APP_NAME,
    ENV,
    GEONAMES_USER,
)
from app.webapp.models.witness import Witness
from app.webapp.utils.constants import MANIFEST_V2
from app.webapp.utils.functions import credentials, list_to_txt
from app.webapp.utils.logger import console, log, get_time
from app.webapp.utils.iiif.annotation import (
    format_canvas_annos,
    index_annotations,
    get_anno_img,
    formatted_annotations,
    anno_request,
    process_anno,
)
import requests


def admin_app(request):
    return redirect("admin:index")


def manifest_digitization(request, digit_ref):
    match = re.search(r"_[a-zA-Z]{3}(\d+)", digit_ref)
    if not match:
        return JsonResponse(
            {
                "response": f"Wrong format of digitization reference:{digit_ref}",
                "reason": "Reference must follow this format: {witness_abbr}{witness_id}_{digit_abbr}{digit_id}",
            },
            safe=False,
        )
    digit_id = int(match.group(1))
    digit = Digitization.objects.filter(pk=digit_id).first()
    if not digit:
        return JsonResponse(
            {"response": f"No digitization matching the id #{digit_id}"},
            safe=False,
        )

    if digit_ref != digit.get_ref():
        return JsonResponse(
            {
                "response": f"Wrong reference for digitization #{digit_id}",
                "reason": "Reference must follow this format: {witness_abbr}{witness_id}_{digit_abbr}{digit_id}",
            },
            safe=False,
        )
    return JsonResponse(digit.gen_manifest_json())


def manifest_annotation(request, version, anno_ref):
    # TODO: better handling of wrong references as above
    anno_id = anno_ref.split("_")[-1].replace("anno", "")
    anno = get_object_or_404(Annotation, pk=anno_id)
    if anno_ref == anno.get_ref():
        return JsonResponse(anno.gen_manifest_json(version=check_version(version)))
    return JsonResponse(
        {"response": f"Wrong reference for Annotation #{anno_id}"}, safe=False
    )


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
            # process file and create Annotation record
            return JsonResponse({"response": "OK"}, status=200)
    else:
        return JsonResponse({"message": "Invalid request"}, status=400)


def export_anno_img(request, anno_id):
    anno = get_object_or_404(Annotation, pk=anno_id)
    annotations = get_anno_img(anno)
    return list_to_txt(annotations, anno.get_ref())


def export_digit_img(request, digit_id):
    digit = get_object_or_404(Digitization, pk=digit_id)
    annotations = []
    for anno in digit.get_annotations():
        annotations.extend(get_anno_img(anno))
    return list_to_txt(annotations, digit.get_ref())


def export_wit_img(request, wit_id):
    wit = get_object_or_404(Witness, pk=wit_id)
    annotations = []
    for anno in wit.get_annotations():
        annotations.extend(get_anno_img(anno))
    return list_to_txt(annotations, wit.get_ref())


def canvas_annotations(request, version, anno_ref, canvas_nb):
    anno_id = anno_ref.split("_")[-1].replace("anno", "")
    anno = get_object_or_404(Annotation, pk=anno_id)
    return JsonResponse(format_canvas_annos(anno, canvas_nb, version))


def populate_annotation(request, anno_id):
    """
    Populate annotation store from IIIF Annotation List
    """
    if not ENV("DEBUG"):
        credentials(f"{SAS_APP_URL}/", ENV("SAS_USERNAME"), ENV("SAS_PASSWORD"))

    anno = get_object_or_404(Annotation, pk=anno_id)
    return HttpResponse(status=200 if index_annotations(anno) else 500)


def validate_annotation(request, anno_id):
    """
    Validate the manually corrected annotations
    """
    try:
        anno = get_object_or_404(Annotation, pk=anno_id)
        anno.is_validated = True
        anno.save()
        return HttpResponse(status=200)
    except Exception as e:
        return HttpResponse(f"An error occurred: {e}", status=500)


def witness_sas_annotations(request, anno_id):
    anno = get_object_or_404(Annotation, pk=anno_id)
    _, canvas_annos = formatted_annotations(anno)
    return JsonResponse(canvas_annos, safe=False)


@login_required(login_url=f"/{APP_NAME}-admin/login/")
def show_annotations(request, anno_id):
    anno = get_object_or_404(Annotation, pk=anno_id)

    if not ENV("DEBUG"):
        credentials(f"{SAS_APP_URL}/", ENV("SAS_USERNAME"), ENV("SAS_PASSWORD"))

    bboxes, canvas_annos = formatted_annotations(anno)

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
            # "wit_type": wit_type,
            # "wit_obj": witness,
            "page_annos": page_annos,
            "bboxes": json.dumps(bboxes),
            "url_manifest": anno.gen_manifest_url(version=MANIFEST_V2),
        },
    )


def test(request, wit_id, wit_type):
    start = get_time()
    model = Annotation
    # try:
    #     wit_id = int(wit_id)
    #     if int(wit_id) == 0:
    #         annos = model.objects.all()
    #     else:
    #         annos = [get_object_or_404(model, pk=anno_id)]
    # except ValueError as e:
    #     console(f"[test] wit_id is not an integer: {e}")
    #     return JsonResponse(
    #         {"response": f"wit_id is not an integer: {wit_id}", e},
    #         safe=False,
    #     )
    #
    # threads = []
    # wit_ids = []
    # # for witness in witnesses:
    # #     if not witness.manifest_final:
    # #         wit_ids.append(witness.id)
    # #         thread = threading.Thread(
    # #             target=check_indexation_annos, args=(digit, True)
    # #         )
    # #         thread.start()
    # #         threads.append(thread)

    return JsonResponse(
        {"response": f"Execution time: {start} > {get_time()}"},
        safe=False,
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


def search_similarity(request, experiment_id):
    # Call search_similarity task
    pass


# TODO: create test to find integrity of a manuscript:
#  if it has the correct number of images, if all its images are img files
#  if annotations were correctly defined (same img name in file that images on server)
