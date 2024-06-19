import json
import os
import re
import zipfile
from os.path import exists

from celery.result import AsyncResult
from dal import autocomplete

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_GET

from app.webapp.models.regions import Regions, check_version
from app.webapp.filters import WitnessFilter
from app.webapp.models.digitization import Digitization
from app.config.settings import (
    SAS_APP_URL,
    APP_NAME,
    ENV,
    GEONAMES_USER,
    APP_LANG,
)
from app.webapp.models.edition import Edition
from app.webapp.models.language import Language
from app.webapp.models.region_pair import RegionPair
from app.webapp.models.witness import Witness
from app.webapp.utils.constants import MANIFEST_V2, MAX_ROWS
from app.webapp.utils.functions import (
    credentials,
    list_to_txt,
    get_json,
    cls,
    delete_files,
    zip_img,
    sort_key,
    zip_images_and_files,
    is_url,
)

from app.webapp.utils.iiif import parse_ref, gen_iiif_url
from app.webapp.utils.logger import log
from app.webapp.utils.iiif.annotation import (
    format_canvas_annotations,
    index_regions,
    delete_regions,
    process_regions,
    formatted_annotations,
)
from app.webapp.utils.regions import (
    get_regions_img,
    create_empty_regions,
)

from app.webapp.utils.paths import REGIONS_PATH, MEDIA_DIR, SCORES_PATH
from app.webapp.utils.similarity import (
    similarity_request,
    get_regions_urls,
    check_score_files,
    check_computed_pairs,
    get_compared_regions,
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
        else "{witness_abbr}{witness_id}_{digit_abbr}{digit_id}_anno{regions_id}"
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
                "response": f"Wrong info given in reference for digitization #{digit_id}",
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


@user_passes_test(is_superuser)
@csrf_exempt
def reindex_regions(request, obj_ref):
    """
    To reindex regions from a text file named after <obj_ref>
    either to create a Regions obj from a regions txt file if obj_ref is a digit_ref
    or to delete then create a new regions file if obj_ref is a regions_ref
    """
    passed, obj = check_ref(obj_ref, "Regions")
    if not passed:
        return JsonResponse(obj)

    regions = obj if cls(obj) == Regions else None
    if regions:
        try:
            delete_regions(regions)
        except Exception as e:
            return JsonResponse(
                {"error": f"Failed to delete regions #{regions.id}: {e}"}
            )

    digit = regions.get_digit() if regions else obj
    if not digit:
        return JsonResponse(
            {"error": f"Failed to retrieve digitization for regions #{obj_ref}"}
        )

    if exists(f"{REGIONS_PATH}/{obj_ref}.txt"):
        try:
            with open(f"{REGIONS_PATH}/{obj_ref}.txt", "r") as file:
                process_regions(file.read(), digit)
            delete_files(f"{REGIONS_PATH}/{obj_ref}.txt")

            return JsonResponse({"message": "Regions were re-indexed."})

        except Exception as e:
            return JsonResponse(
                {"error": f"Failed to index regions for digit #{digit.id}: {e}"}
            )
    else:
        create_empty_regions(digit)

    return JsonResponse({"error": f"No regions file for reference #{obj_ref}."})


@user_passes_test(is_superuser)
def index_regions(request, regions_ref=None):
    """
    Index the content of a regions txt file named after the regions_ref (wit<id>_<digit><id>_anno<id>.txt) into SAS
    without creating an annotation record if one is already existing
    If no regions_ref is provided all regions files for mediafiles/regions are indexed
    """

    regions_file = os.listdir(REGIONS_PATH) if not regions_ref else [regions_ref]

    indexed_regions = []
    not_indexed_regions = []

    for file in regions_file:
        a_ref = file.replace(".txt", "")
        ref = parse_ref(a_ref)
        if not ref or not ref["regions"]:
            # if there is no regions_id in the ref, pass
            not_indexed_regions.append(a_ref)
            continue
        regions_id = ref["regions"][1]
        regions = Regions.objects.filter(pk=regions_id).first()
        if not regions:
            digit = Digitization.objects.filter(pk=ref["digit"][1]).first()
            if not digit:
                # if there is no digit corresponding to the ref, pass
                not_indexed_regions.append(a_ref)
                continue
            regions = Regions(
                id=regions_id, digitization=digit, model="CHANGE THIS VALUE"
            )
            regions.save()

        from app.webapp.tasks import reindex_from_file

        reindex_from_file.delay(regions_id)
        indexed_regions.append(a_ref)

    return JsonResponse(
        {
            "All": regions_file,
            "Indexed": indexed_regions,
            "Not indexed": not_indexed_regions,
        }
    )


@user_passes_test(is_superuser)
def delete_annotations_regions(request, obj_ref):
    """
    Unindex SAS annotations + delete Regions record from the database
    """
    passed, obj = check_ref(obj_ref, "Regions")
    if not passed:
        return JsonResponse(obj)

    regions = obj if cls(obj) == Regions else None
    if regions:
        try:
            delete_regions(regions)
        except Exception as e:
            return JsonResponse(
                {
                    "error": f"Failed to delete regions file and annotations for reference #{regions.id}: {e}"
                }
            )

    return JsonResponse({"error": f"No regions file for reference #{obj_ref}."})


def get_regions_img_list(request, regions_ref):
    """
    return something like that
    {
        "wit1_man191_0009_166,1325,578,516": ""https://eida.obspm.fr/iiif/2/wit1_man191_0009.jpg/166,1325,578,516/full/0/default.jpg"",
        "wit1_man191_0027_1143,2063,269,245": "https://eida.obspm.fr/iiif/2/wit1_man191_0027.jpg/1143,2063,269,245/full/0/default.jpg",
        "wit1_man191_0031_857,2013,543,341": "https://eida.obspm.fr/iiif/2/wit1_man191_0031.jpg/857,2013,543,341/full/0/default.jpg",
        "img_name": "..."
    }
    """

    passed, regions = check_ref(regions_ref, "Regions")
    if not passed:
        return JsonResponse(regions)

    try:
        regions_dict = get_regions_urls(regions)
    except Exception as e:
        error = f"[get_regions_img_list] Couldn't generate list of regions images for {regions_ref}"
        log(error, e)
        return JsonResponse({"response": error, "reason": e}, safe=False)

    return JsonResponse(regions_dict, status=200, safe=False)


@user_passes_test(is_superuser)
def send_similarity(request, regions_refs):
    """
    To relaunch similarity request in case the automatic process has failed
    """

    regions = [
        region
        for (passed, region) in [check_ref(ref, "Regions") for ref in regions_refs]
        if passed
    ]

    if not len(regions):
        return JsonResponse(
            {
                "response": f"No corresponding regions in the database for {regions_refs}"
            },
            safe=False,
        )

    if len(check_computed_pairs(regions_refs)) == 0:
        return JsonResponse(
            {"response": f"All similarity pairs were computed for {regions_refs}"},
            safe=False,
        )

    try:
        if similarity_request(regions):
            return JsonResponse(
                {"response": f"Successful similarity request for {regions_refs}"},
                safe=False,
            )
        return JsonResponse(
            {"response": f"Failed to send similarity request for {regions_refs}"},
            safe=False,
        )

    except Exception as e:
        error = f"[send_similarity] Couldn't send request for {regions_refs}"
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
            for regions_refs, file in request.FILES.items():
                with open(f"{SCORES_PATH}/{regions_refs}.npy", "wb") as destination:
                    filenames.append(regions_refs)
                    for chunk in file.chunks():
                        destination.write(chunk)

            check_score_files(filenames)
            return JsonResponse({"message": "Score files received successfully"})
        except Exception as e:
            log("[receive_similarity] Error saving score files", e)
            return JsonResponse({"message": "Error saving score files"}, status=500)
    return JsonResponse({"message": "Invalid request"}, status=400)


def task_status(request, task_id):
    task = AsyncResult(task_id)
    if task.ready():
        try:
            result = json.dumps(task.result)
        except TypeError as e:
            log(task.result)
            log(f"[task_status] Could not parse result for {task_id}", e)
            return JsonResponse({"status": "failed", "result": ""})
        return JsonResponse({"status": "success", "result": result})
    return JsonResponse({"status": "running"})


def compute_score(request):
    from app.webapp.tasks import compute_similarity_scores

    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            regions_refs = data.get("regionsRefs", [])
            max_rows = int(data.get("maxRows", 50))
            show_checked_ref = data.get("showCheckedRef", True)
            if len(regions_refs) == 0:
                return JsonResponse(
                    {"error": "No regions_ref to retrieve score"}, status=400
                )
            return JsonResponse(
                compute_similarity_scores(regions_refs, max_rows, show_checked_ref),
                status=200,
            )
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=400)


@login_required(login_url=f"/{APP_NAME}-admin/login/")
def show_similarity(request, regions_ref):
    refs = get_compared_regions(regions_ref)
    regions = {
        region.get_ref(): region.__str__()
        for (passed, region) in [check_ref(ref, "Regions") for ref in refs]
        if passed
    }

    return render(
        request,
        "show_similarity.html",
        context={
            "title": "Similarity search result"
            if APP_LANG == "en"
            else "Résultat de recherche de similarité",
            "regions": dict(sorted(regions.items())),
            "checked_ref": regions_ref,
            "checked_ref_title": regions[regions_ref],
            "regions_refs": json.dumps(refs),
        },
    )


def export_regions_img(request, regions_id):
    regions = get_object_or_404(Regions, pk=regions_id)
    images = get_regions_img(regions)
    return list_to_txt(images, regions.get_ref())


def export_digit_img(request, digit_id):
    digit = get_object_or_404(Digitization, pk=digit_id)
    regions = []
    for region in digit.get_regions():
        regions.extend(get_regions_img(region))
    return list_to_txt(regions, digit.get_ref())


def export_wit_img(request, wit_id):
    wit = get_object_or_404(Witness, pk=wit_id)
    regions = []
    for region in wit.get_regions():
        regions.extend(get_regions_img(region))
    return list_to_txt(regions, wit.get_ref())


def canvas_annotations(request, version, regions_ref, canvas_nb):
    regions_id = regions_ref.split("_")[-1].replace("anno", "")
    regions = get_object_or_404(Regions, pk=regions_id)
    return JsonResponse(format_canvas_annotations(regions, canvas_nb))


def populate_annotation(request, regions_id):
    """
    Populate annotation store from IIIF Annotation List
    """
    if not ENV("DEBUG"):
        credentials(f"{SAS_APP_URL}/", ENV("SAS_USERNAME"), ENV("SAS_PASSWORD"))

    regions = get_object_or_404(Regions, pk=regions_id)
    return HttpResponse(status=200 if index_regions(regions) else 500)


def validate_regions(request, regions_ref):
    """
    Validate the manually corrected regions
    """
    try:
        passed, regions = check_ref(regions_ref, "Regions")
        if not passed:
            return HttpResponse(regions, status=500)
        regions.is_validated = True
        regions.save()
        return HttpResponse(status=200)
    except Exception as e:
        return HttpResponse(f"An error occurred: {e}", status=500)


def witness_sas_annotations(request, regions_id):
    regions = get_object_or_404(Regions, pk=regions_id)
    _, canvas_annotations = formatted_annotations(regions)
    return JsonResponse(canvas_annotations, safe=False)


@login_required(login_url=f"/{APP_NAME}-admin/login/")
def show_regions(request, regions_ref):
    passed, regions = check_ref(regions_ref, "Regions")
    if not passed:
        # if cls(regions) == Digitization:
        #     create_empty_regions(regions)
        return JsonResponse(regions)

    if not ENV("DEBUG"):
        credentials(f"{SAS_APP_URL}/", ENV("SAS_USERNAME"), ENV("SAS_PASSWORD"))

    bboxes, canvas_annotations = formatted_annotations(regions)

    paginator = Paginator(canvas_annotations, 50)
    try:
        page_regions = paginator.page(request.GET.get("page"))
    except PageNotAnInteger:
        page_regions = paginator.page(1)
    except EmptyPage:
        page_regions = paginator.page(paginator.num_pages)

    return render(
        request,
        "show.html",
        context={
            "regions": regions,
            "page_regions": page_regions,
            "bboxes": json.dumps(bboxes),
            "url_manifest": regions.gen_manifest_url(version=MANIFEST_V2),
        },
    )


@login_required(login_url=f"/{APP_NAME}-admin/login/")
def show_all_regions(request, regions_ref):
    passed, regions = check_ref(regions_ref, "Regions")
    if not passed:
        return JsonResponse(regions)

    if not ENV("DEBUG"):
        credentials(f"{SAS_APP_URL}/", ENV("SAS_USERNAME"), ENV("SAS_PASSWORD"))

    _, all_annotations = formatted_annotations(regions)
    all_regions = [
        (canvas_nb, coord, img_file)
        for canvas_nb, coord, img_file in all_annotations
        if coord
    ]

    paginator = Paginator(all_regions, 50)
    try:
        page_regions = paginator.page(request.GET.get("page"))
    except PageNotAnInteger:
        page_regions = paginator.page(1)
    except EmptyPage:
        page_regions = paginator.page(paginator.num_pages)

    return render(
        request,
        "show_regions.html",
        context={
            "regions": regions,
            "page_regions": page_regions,
            "all_regions": all_regions,
            "url_manifest": regions.gen_manifest_url(version=MANIFEST_V2),
            "regions_ref": regions_ref,
        },
    )


@login_required(login_url=f"/{APP_NAME}-admin/login/")
def show_vectorization(request, regions_ref):
    passed, regions = check_ref(regions_ref, "Regions")
    if not passed:
        return JsonResponse(regions)

    if not ENV("DEBUG"):
        credentials(f"{SAS_APP_URL}/", ENV("SAS_USERNAME"), ENV("SAS_PASSWORD"))

    _, all_annotations = formatted_annotations(regions)
    all_regions = [
        (canvas_nb, coord, img_file)
        for canvas_nb, coord, img_file in all_annotations
        if coord
    ]

    return render(
        request,
        "show_vectorization.html",
        context={
            "regions": regions,
            "all_regions": all_regions,
            "regions_ref": regions_ref,
        },
    )


@login_required(login_url=f"/{APP_NAME}-admin/login/")
def export_all_regions(request, regions_ref):
    passed, regions = check_ref(regions_ref, "Regions")
    if not passed:
        return JsonResponse(regions)

    if not ENV("DEBUG"):
        credentials(f"{SAS_APP_URL}/", ENV("SAS_USERNAME"), ENV("SAS_PASSWORD"))

    urls_list = []

    _, all_annotations = formatted_annotations(regions)
    all_regions = [
        (canvas_nb, coord, img_file)
        for canvas_nb, coord, img_file in all_annotations
        if coord
    ]

    for canvas_nb, coord, img_file in all_regions:
        urls_list.extend(gen_iiif_url(img_file, 2, f"{c[0]}/full/0") for c in coord)

    return zip_img(urls_list)


@login_required(login_url=f"/{APP_NAME}-admin/login/")
def export_selected_regions(request):
    urls_list = json.loads(request.POST.get("listeURL"))
    return zip_img(urls_list)


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

        suggestions = []
        try:
            for suggestion in data["geonames"]:
                suggestions.append(
                    f"{suggestion['name']} | {suggestion.get('countryCode', '')}"
                )

            return suggestions
        except Exception as e:
            log("[place_autocomplete] Error fetching Geonames data.", e)
            suggestions.append("Error fetching geographical data.")

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
        # Ensure the user is authenticated
        if not self.request.user.is_authenticated:
            return Language.objects.none()

        qs = Language.objects.all()

        if self.q:
            qs = qs.filter(lang__icontains=self.q)

        return qs


@require_GET
def retrieve_category(request):
    img_1, img_2 = sorted(
        [request.GET.get("img_1"), request.GET.get("img_2")], key=sort_key
    )

    try:
        region_pair = RegionPair.objects.get(img_1=img_1, img_2=img_2)
        category = region_pair.category
        category_x = region_pair.category_x
    except RegionPair.DoesNotExist:
        category = None
        category_x = []

    return JsonResponse({"category": category, "category_x": category_x})


@csrf_exempt
def save_category(request):
    if request.method == "POST":
        data = json.loads(request.body)
        img_1, img_2 = sorted([data.get("img_1"), data.get("img_2")], key=sort_key)
        regions_ref_1, regions_ref_2 = sorted(
            [data.get("regions_ref_1"), data.get("regions_ref_2")], key=sort_key
        )
        category = data.get("category")
        category_x = data.get("category_x")
        user_id = request.user.id

        region_pair, created = RegionPair.objects.get_or_create(
            img_1=img_1,
            img_2=img_2,
            defaults={
                "regions_ref_1": regions_ref_1,
                "regions_ref_2": regions_ref_2,
            },
        )

        region_pair.category = int(category) if category else None

        # If the user's id doesn't exist in category_x, append it
        if category_x is not None:
            if user_id not in region_pair.category_x:
                region_pair.category_x.append(user_id)
            region_pair.category_x = sorted(region_pair.category_x)
        else:  # If category_x is None, remove the user's id if it exists
            if user_id in region_pair.category_x:
                region_pair.category_x.remove(user_id)

        region_pair.save()

        if created:
            return JsonResponse(
                {"status": "success", "message": "New region pair created"}, status=200
            )
        return JsonResponse(
            {"status": "success", "message": "Existing region pair updated"}, status=200
        )


def rgpd(request):
    return render(request, "rgpd.html")


def legacy_manifest(request, old_id):
    if not os.path.isfile(f"{MEDIA_DIR}/manifest/{old_id}.json"):
        return JsonResponse({})
    with open(f"{MEDIA_DIR}/manifest/{old_id}.json", "r") as manifest:
        return JsonResponse(json.loads(manifest.read()))


@login_required(login_url=f"/{APP_NAME}-admin/login/")
def advanced_search(request):
    witness_list = Witness.objects.order_by("id")
    witness_filter = WitnessFilter(request.GET, queryset=witness_list)

    paginator = Paginator(witness_filter.qs, 3)  # 3 items per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "title": "Advanced search" if APP_LANG == "en" else "Recherche avancée",
        "witness_filter": witness_filter,
        "result_count": witness_filter.qs.count(),
        "page_obj": page_obj,
    }
    return render(request, "webapp/search.html", context)


class EditionAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Ensure the user is authenticated
        if not self.request.user.is_authenticated:
            return Edition.objects.none()

        qs = Edition.objects.all()

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs
