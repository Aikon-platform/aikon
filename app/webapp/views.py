import json
import os
import re
from os.path import exists

from dal import autocomplete

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.decorators import login_required, user_passes_test

from app.webapp.models.annotation import Annotation, check_version
from app.webapp.models.digitization import Digitization
from app.config.settings import (
    SAS_APP_URL,
    APP_NAME,
    ENV,
    GEONAMES_USER,
)
from app.webapp.models.language import Language
from app.webapp.models.place import Place
from app.webapp.models.witness import Witness
from app.webapp.utils.constants import MANIFEST_V2, MAX_ROWS
from app.webapp.utils.functions import (
    credentials,
    list_to_txt,
    get_json,
    cls,
    delete_files,
)
from app.webapp.utils.iiif import parse_ref
from app.webapp.utils.logger import console, log, get_time
from app.webapp.utils.iiif.annotation import (
    format_canvas_annos,
    index_annotations,
    get_anno_img,
    formatted_annotations,
    anno_request,
    process_anno,
    delete_annos,
    create_empty_anno,
    get_manifest_annos,
    check_indexation_annos,
)

from app.webapp.utils.paths import ANNO_PATH, MEDIA_DIR


def is_superuser(user):
    return user.is_superuser


def admin_app(request):
    return redirect("admin:index")


def check_ref(obj_ref, obj="Digitization"):
    ref = parse_ref(obj_ref)
    ref_format = (
        "{witness_abbr}{witness_id}_{digit_abbr}{digit_id}"
        if obj == "Digitization"
        else "{witness_abbr}{witness_id}_{digit_abbr}{digit_id}_anno{anno_id}"
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

    if obj == "Digitization" or ref["anno"] is None:
        if obj_ref != digit.get_ref():
            return False, {
                "response": f"Wrong info given in reference for digitization #{digit_id}",
                "reason": f"Reference must follow this format: {ref_format}",
            }
        return True, digit

    anno_id = ref["anno"][1]
    anno = Annotation.objects.filter(pk=anno_id).first()
    if not anno:
        return False, {"response": f"No annotation matching the id #{anno_id}"}

    if obj == "Annotation":
        if obj_ref != anno.get_ref():
            return False, {
                "response": f"Wrong info given in reference for annotation #{anno_id}",
                "reason": f"Reference must follow this format: {ref_format}",
            }
        return True, anno

    return False, {"response": f"Nothing to retrieve for {obj} #{obj_ref}"}


def manifest_digitization(request, digit_ref):
    # TODO make difference if witness is not public
    passed, digit = check_ref(digit_ref)
    if not passed:
        return JsonResponse(digit, safe=False)

    return JsonResponse(digit.gen_manifest_json())


def manifest_annotation(request, version, anno_ref):
    # TODO make difference if witness is not public
    passed, anno = check_ref(anno_ref, "Annotation")
    if not passed:
        return JsonResponse(anno, safe=False)

    return JsonResponse(anno.gen_manifest_json(version=check_version(version)))


@user_passes_test(is_superuser)
def send_anno(request, digit_ref):
    """
    To relaunch annotations in case the automatic annotation failed
    """
    passed, digit = check_ref(digit_ref)
    if not passed:
        return JsonResponse(digit, safe=False)

    error = {"response": f"Failed to send annotation request for digit #{digit.id}"}
    try:
        status = anno_request(digit)
    except Exception as e:
        error["cause"] = e
        return JsonResponse(error, safe=False)

    if status:
        return JsonResponse(
            {"response": f"Annotations were relaunched for digit #{digit.id}"},
            safe=False,
        )
    return JsonResponse(error, safe=False)


@user_passes_test(is_superuser)
def reindex_anno(request, obj_ref):
    """
    To reindex annotations from a text file named after <obj_ref>
    either to create an Annotation obj from an annotation txt file if obj_ref is a digit_ref
    or to delete then create a new annotation if obj_ref is an anno_ref
    """
    passed, obj = check_ref(obj_ref, "Annotation")
    if not passed:
        return JsonResponse(obj)

    anno = obj if cls(obj) == Annotation else None
    if anno:
        try:
            delete_annos(anno)
        except Exception as e:
            return JsonResponse(
                {"error": f"Failed to delete annotation #{anno.id}: {e}"}
            )

    digit = anno.get_digit() if anno else obj
    if not digit:
        return JsonResponse(
            {"error": f"Failed to retrieve digitization for annotation #{obj_ref}"}
        )

    if exists(f"{ANNO_PATH}/{obj_ref}.txt"):
        try:
            with open(f"{ANNO_PATH}/{obj_ref}.txt", "r") as file:
                process_anno(file.read(), digit)
            delete_files(f"{ANNO_PATH}/{obj_ref}.txt")

            return JsonResponse({"message": "Annotations were re-indexed."})

        except Exception as e:
            return JsonResponse(
                {"error": f"Failed to index annotations for digit #{digit.id}: {e}"}
            )
    else:
        create_empty_anno(digit)

    return JsonResponse({"error": f"No annotation file for reference #{obj_ref}."})


def index_anno(request, anno_ref=None):
    """
    Index the content of a txt file named after the anno_ref into SAS
    without creating an annotation record if one is already existing
    If no anno_ref is provided all anno files for mediafiles/annotation are indexed
    """
    anno_files = os.listdir(ANNO_PATH) if not anno_ref else [anno_ref]

    indexed_anno = []
    not_indexed_anno = []

    for file in anno_files:
        a_ref = file.replace(".txt", "")
        ref = parse_ref(a_ref)
        if not ref or not ref["anno"]:
            # if there is no anno_id in the ref, pass
            not_indexed_anno.append(a_ref)
            continue
        anno_id = ref["anno"][1]
        anno = Annotation.objects.filter(pk=anno_id).first()
        if not anno:
            digit = Digitization.objects.filter(pk=ref["digit"][1]).first()
            if not digit:
                # if there is no digit corresponding to the ref, pass
                not_indexed_anno.append(a_ref)
                continue
            anno = Annotation(id=anno_id, digitization=digit, model="CHANGE THIS VALUE")
            anno.save()

        try:
            if check_indexation_annos(anno, True):
                indexed_anno.append(a_ref)
            else:
                not_indexed_anno.append(a_ref)
        except Exception as e:
            not_indexed_anno.append(a_ref)
            log(f"[index_anno] Failed to index annotations for ref #{a_ref}", e)

    return JsonResponse(
        {"All": anno_files, "Indexed": indexed_anno, "Not indexed": not_indexed_anno}
    )


def delete_send_anno(request, anno_ref):
    """
    To delete images on the GPU and relaunch annotations
    """
    passed, anno = check_ref(anno_ref, "Annotation")
    if not passed:
        return JsonResponse(anno)
    # TODO redo entirely
    # manifest_url = f"{VHS_APP_URL}/{APP_NAME}/iiif/{MANIFEST_AUTO}/{wit_type}/{wit_id}/manifest.json"
    # try:
    #     requests.post(
    #         url=f"{API_GPU_URL}/delete_detect",
    #         headers={"X-API-Key": EXAPI_KEY},
    #         data={"manifest_url": manifest_url},
    #     )
    # except Exception as e:
    #     log(
    #         f"[delete_send_anno] Failed to send deletion and annotation request for {wit_type} #{wit_id}: {e}"
    #     )
    #     return JsonResponse(
    #         {
    #             "response": f"Failed to send deletion and annotation request for {wit_type} #{wit_id}",
    #             "cause": e,
    #         },
    #         safe=False,
    #     )

    return JsonResponse(
        {
            "response": f"Images were deleted and annotations were relaunched for Annotation #{anno.id}"
        },
        safe=False,
    )


@csrf_exempt
def receive_anno(request, digit_ref):
    passed, digit = check_ref(digit_ref)
    if not passed:
        return JsonResponse(digit)

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
    return JsonResponse(format_canvas_annos(anno, canvas_nb))


def populate_annotation(request, anno_id):
    """
    Populate annotation store from IIIF Annotation List
    """
    if not ENV("DEBUG"):
        credentials(f"{SAS_APP_URL}/", ENV("SAS_USERNAME"), ENV("SAS_PASSWORD"))

    anno = get_object_or_404(Annotation, pk=anno_id)
    return HttpResponse(status=200 if index_annotations(anno) else 500)


def validate_annotation(request, anno_ref):
    """
    Validate the manually corrected annotations
    """
    try:
        passed, anno = check_ref(anno_ref, "Annotation")
        if not passed:
            return HttpResponse(anno, status=500)
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
def show_annotations(request, anno_ref):
    passed, anno = check_ref(anno_ref, "Annotation")
    if not passed:
        # if cls(anno) == Digitization:
        #     create_empty_anno(anno)
        return JsonResponse(anno)

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
        "show.html",
        context={
            "anno": anno,
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
        name = self.forwarded.get("name")
        query = name if name else self.q
        data = get_json(
            f"http://api.geonames.org/searchJSON?q={query}&maxRows={MAX_ROWS}&username={GEONAMES_USER}"
        )
        # TODO use try/except to avoid bug if geonames key doesn't exist
        suggestions = []
        for suggestion in data["geonames"]:
            suggestions.append(suggestion["name"])

        return suggestions


def retrieve_place_info(request):
    """
    Extract the relevant information (country, latitude, longitude) from the Geonames API response
    """
    name = request.GET.get("name")
    if name:
        data = get_json(
            f"http://api.geonames.org/searchJSON?q={name}&maxRows={MAX_ROWS}&username={GEONAMES_USER}"
        )
        country = data["geonames"][0].get("countryName")
        latitude = data["geonames"][0].get("lat")
        longitude = data["geonames"][0].get("lng")

        return JsonResponse(
            {
                "country": country,
                "latitude": f"{float(latitude):.4f}",
                "longitude": f"{float(longitude):.4f}",
            }
        )

    return JsonResponse({"country": "", "latitude": "", "longitude": ""})


class LanguageAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Language.objects.all()

        if self.q:
            qs = qs.filter(lang__icontains=self.q)

        return qs


def search_similarity(request, experiment_id):
    # Call search_similarity task
    pass


def rgpd(request):
    return render(request, "rgpd.html")


def legacy_manifest(request, old_id):
    if not os.path.isfile(f"{MEDIA_DIR}/manifest/{old_id}.json"):
        return JsonResponse({})
    with open(f"{MEDIA_DIR}/manifest/{old_id}.json", "r") as manifest:
        return JsonResponse(json.loads(manifest.read()))


# TODO: create test to find integrity of a manuscript:
#  if it has the correct number of images, if all its images are img files
#  if annotations were correctly defined (same img name in file that images on server)
