import json
import os
from os.path import exists

from celery.result import AsyncResult
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
from app.webapp.utils.logger import log
from app.webapp.utils.iiif.annotation import (
    format_canvas_annos,
    index_annotations,
    get_anno_img,
    formatted_annotations,
    anno_request,
    process_anno,
    delete_annos,
    create_empty_anno,
    check_anno_file,
    delete_anno_request,
)

from app.webapp.utils.paths import ANNO_PATH, MEDIA_DIR, SCORES_PATH
from app.webapp.utils.similarity import (
    similarity_request,
    get_annotation_urls,
    check_score_files,
    check_computed_pairs,
)


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


@user_passes_test(is_superuser)
def index_anno(request, anno_ref=None):
    """
    Index the content of a txt file named after the anno_ref (wit<id>_<digit><id>_anno<id>.txt) into SAS
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

        from app.webapp.tasks import reindex_from_file

        reindex_from_file.delay(anno_id)
        indexed_anno.append(a_ref)

    return JsonResponse(
        {"All": anno_files, "Indexed": indexed_anno, "Not indexed": not_indexed_anno}
    )


@user_passes_test(is_superuser)
def delete_send_anno(request, digit_ref):
    """
    To delete images on the GPU and relaunch annotations
    """
    passed, digit = check_ref(digit_ref, "Annotation")
    if not passed:
        return JsonResponse(digit)

    error = {
        "response": f"Failed to send deletion and retry request for annotations #{digit.id}"
    }

    try:
        status = delete_anno_request(digit)
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
def delete_annotation(request, obj_ref):
    """
    Unindex SAS annotations + delete Annotation record from the database
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

    return JsonResponse({"error": f"No annotation file for reference #{obj_ref}."})


@csrf_exempt
def receive_anno(request, digit_ref):
    """
    Process the result of the API containing digitation annotations
    """
    passed, digit = check_ref(digit_ref)
    if not passed:
        return JsonResponse(digit)

    if request.method == "POST":
        try:
            annotation_file = request.FILES["annotation_file"]
        except Exception as e:
            log("[receive_anno] No annotation file received for", e)
            return JsonResponse({"message": "No annotation file"}, status=400)

        try:
            model = request.POST.get("model", "Unknown model")
        except Exception as e:
            log("[receive_anno] Unable to retrieve model param", e)
            model = "Unknown model"
        file_content = annotation_file.read()
        file_content = file_content.decode("utf-8")

        if check_anno_file(file_content):
            from app.webapp.tasks import process_anno_file

            process_anno_file.delay(file_content, digit.id, model)
            return JsonResponse({"response": "OK"}, status=200)
            # if process_anno(file_content, digit, model):
            #     return JsonResponse({"response": "OK"}, status=200)
        return JsonResponse(
            {"message": "Could not process annotation file"}, status=400
        )
    else:
        return JsonResponse({"message": "Invalid request"}, status=400)


def get_annos_img_list(request, anno_ref):
    """
    return something like that
    {
        "wit1_man191_0009_166,1325,578,516": ""https://eida.obspm.fr/iiif/2/wit1_man191_0009.jpg/166,1325,578,516/full/0/default.jpg"",
        "wit1_man191_0027_1143,2063,269,245": "https://eida.obspm.fr/iiif/2/wit1_man191_0027.jpg/1143,2063,269,245/full/0/default.jpg",
        "wit1_man191_0031_857,2013,543,341": "https://eida.obspm.fr/iiif/2/wit1_man191_0031.jpg/857,2013,543,341/full/0/default.jpg",
        "img_name": "..."
    }
    """

    passed, anno = check_ref(anno_ref, "Annotation")
    if not passed:
        return JsonResponse(anno)

    try:
        anno_dict = get_annotation_urls(anno)
    except Exception as e:
        error = f"[get_annos_img_list] Couldn't generate list of annotation images for {anno_ref}"
        log(error, e)
        return JsonResponse({"response": error, "reason": e}, safe=False)

    return JsonResponse(anno_dict, status=200, safe=False)


@user_passes_test(is_superuser)
def send_similarity(request, anno_refs):
    """
    To relaunch similarity request in case the automatic process has failed
    """

    annos = [
        anno
        for (passed, anno) in [check_ref(ref, "Annotation") for ref in anno_refs]
        if passed
    ]

    if not len(annos):
        return JsonResponse(
            {
                "response": f"No corresponding annotation in the database for {anno_refs}"
            },
            safe=False,
        )

    if len(check_computed_pairs(anno_refs)) == 0:
        return JsonResponse(
            {"response": f"All similarity pairs were computed for {anno_refs}"},
            safe=False,
        )

    try:
        if similarity_request(annos):
            return JsonResponse(
                {"response": f"Successful similarity request for {anno_refs}"},
                safe=False,
            )
        return JsonResponse(
            {"response": f"Failed to send similarity request for {anno_refs}"},
            safe=False,
        )

    except Exception as e:
        error = f"[send_similarity] Couldn't send request for {anno_refs}"
        log(error, e)

        return JsonResponse({"response": error, "reason": e}, safe=False)


@csrf_exempt
def receive_similarity(request):
    """
    Handle response of the API sending back similarity files
    """
    if request.method == "POST":
        filenames = []
        try:
            for anno_refs, file in request.FILES.items():
                with open(f"{SCORES_PATH}/{anno_refs}.npy", "wb") as destination:
                    filenames.append(anno_refs)
                    for chunk in file.chunks():
                        destination.write(chunk)

            check_score_files(filenames)
            return JsonResponse({"message": "Score files received successfully"})
        except Exception as e:
            log("[receive_similarity] Error saving score files", e)
            return JsonResponse({"message": "Error saving score files"}, status=500)
    return JsonResponse({"message": "Invalid request"}, status=400)


def similarity_status(request, task_id):
    task = AsyncResult(task_id)
    if task.ready():
        try:
            result = json.dumps(task.result)
        except TypeError as e:
            log(task.result)
            log(f"[similarity_status] Could not parse result for {task_id}", e)
            return JsonResponse({"status": "failed", "result": ""})
        return JsonResponse({"status": "success", "result": result})
    return JsonResponse({"status": "running"})


@login_required(login_url=f"/{APP_NAME}-admin/login/")
def show_similarity(request, anno_refs):
    from app.webapp.tasks import compute_similarity_scores
    # WITH CELERY
    scores_task = compute_similarity_scores.delay(anno_refs)
    return render(
        request,
        "similarity.html",
        context={
            "title": f"Similarity scores for {anno_refs}",
            "task_id": scores_task.id,
            "anno_refs": json.dumps(anno_refs),
        },
    )

    # # WITHOUT CELERY
    # annos = [anno for (passed, anno) in [check_ref(ref, "Annotation") for ref in anno_refs] if passed]
    # if not len(annos):
    #     return JsonResponse(
    #         {"response": f"No corresponding annotation in the database for {anno_refs}"},
    #         safe=False
    #     )
    # total_scores = compute_total_similarity(annos, anno_refs)
    # paginator = Paginator(total_scores, 50)
    # try:
    #     page_scores = paginator.page(request.GET.get("page"))
    # except PageNotAnInteger:
    #     page_scores = paginator.page(1)
    # except EmptyPage:
    #     page_scores = paginator.page(paginator.num_pages)
    #
    # return render(
    #     request,
    #     "similarity.html",
    #     context={
    #         "title": f"Similarity scores for {anno_refs}",
    #         "scores": page_scores,
    #         "anno_refs": anno_refs
    #     },
    # )


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


def test(request, wit_ref=None):
    from app.webapp.tasks import test

    test.delay("Hello world.")
    return JsonResponse({"response": "OK"}, status=200)


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
            suggestions.append(
                f"{suggestion['name']} | {suggestion.get('countryCode', '')}"
            )

        return suggestions


def retrieve_place_info(request):
    """
    Extract the relevant information (country, latitude, longitude) from the Geonames API response
    """
    name = request.GET.get("name")
    countryCode = request.GET.get("countryCode")
    if name:
        data = get_json(
            f"http://api.geonames.org/searchJSON?q={name}&country={countryCode}&maxRows={MAX_ROWS}&username={GEONAMES_USER}"
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


def rgpd(request):
    return render(request, "rgpd.html")


def legacy_manifest(request, old_id):
    if not os.path.isfile(f"{MEDIA_DIR}/manifest/{old_id}.json"):
        return JsonResponse({})
    with open(f"{MEDIA_DIR}/manifest/{old_id}.json", "r") as manifest:
        return JsonResponse(json.loads(manifest.read()))
