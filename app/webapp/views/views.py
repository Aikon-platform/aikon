import json
import os
from os.path import exists

import requests
from celery.result import AsyncResult
from dal import autocomplete

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.decorators import login_required, user_passes_test

from app.webapp.models.document_set import DocumentSet
from app.webapp.models.regions import Regions, check_version
from app.webapp.search_filters import WitnessFilter
from app.webapp.models.digitization import Digitization
from app.config.settings import (
    SAS_APP_URL,
    APP_NAME,
    GEONAMES_USER,
    APP_LANG,
    DEBUG,
    SAS_USERNAME,
    SAS_PASSWORD,
    CV_API_URL,
)
from app.webapp.models.edition import Edition
from app.webapp.models.language import Language
from app.webapp.models.treatment import Treatment
from app.webapp.models.witness import Witness
from app.webapp.utils.constants import MANIFEST_V2, MAX_ROWS
from app.webapp.utils.functions import (
    credentials,
    list_to_txt,
    get_json,
    cls,
    delete_files,
    zip_img,
    get_files_with_prefix,
)

from app.webapp.utils.iiif import parse_ref, gen_iiif_url
from app.webapp.utils.logger import log
from app.webapp.utils.iiif.annotation import (
    format_canvas_annotations,
    index_regions,
    delete_regions,
    process_regions,
    formatted_annotations,
    get_regions_annotations,
    reindex_file,
    get_regions_urls,
)
from app.webapp.utils.regions import (
    get_regions_img,
    create_empty_regions,
)

from app.webapp.utils.paths import REGIONS_PATH, MEDIA_DIR


def is_superuser(user):
    return user.is_superuser


def admin_app(request):
    return redirect("admin:index")


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
    TODO differenciate clearly from index_regions
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
def index_witness_regions(request, wit_id):
    wit = get_object_or_404(Witness, pk=wit_id)
    regions_files = sorted(get_files_with_prefix(REGIONS_PATH, f"{wit.get_ref()}_"))
    res = {
        "All": regions_files,
        "Indexed": [],
        "Not indexed": [],
    }
    for file in regions_files:
        passed, a_ref = reindex_file(file)
        res["Indexed" if passed else "Not indexed"].append(a_ref)

    return JsonResponse(res)


@user_passes_test(is_superuser)
def index_regions(request, regions_ref=None):
    """
    Index the content of a regions txt file named after the regions_ref (wit<id>_<digit><id>_anno<id>.txt) into SAS
    without creating an annotation record if one is already existing
    If no regions_ref is provided all regions files for mediafiles/regions are indexed
    """
    regions_files = os.listdir(REGIONS_PATH) if not regions_ref else [regions_ref]

    res = {
        "All": regions_files,
        "Indexed": [],
        "Not indexed": [],
    }

    for file in regions_files:
        passed, a_ref = reindex_file(file)
        res["Indexed" if passed else "Not indexed"].append(a_ref)

    return JsonResponse(res)


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
    if not DEBUG:
        credentials(f"{SAS_APP_URL}/", SAS_USERNAME, SAS_PASSWORD)

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
    _, c_annos = formatted_annotations(regions)
    return JsonResponse(c_annos, safe=False)


@login_required(login_url=f"/{APP_NAME}-admin/login/")
def show_regions(request, regions_ref):
    # NOTE soon to be not used
    passed, regions = check_ref(regions_ref, "Regions")
    if not passed:
        # if cls(regions) == Digitization:
        #     create_empty_regions(regions)
        return JsonResponse(regions)

    if not DEBUG:
        credentials(f"{SAS_APP_URL}/", SAS_USERNAME, SAS_PASSWORD)

    bboxes, c_annos = formatted_annotations(regions)

    paginator = Paginator(c_annos, 50)
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
    # NOTE soon to be not used
    passed, regions = check_ref(regions_ref, "Regions")
    if not passed:
        return JsonResponse(regions)

    if not DEBUG:
        credentials(f"{SAS_APP_URL}/", SAS_USERNAME, SAS_PASSWORD)

    # _, all_annotations = formatted_annotations(regions)
    # all_regions = [
    #     (canvas_nb, coord, img_file)
    #     for canvas_nb, coord, img_file in all_annotations
    #     if coord
    # ]
    all_regions = get_regions_annotations(regions)

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
def export_all_regions(request, regions_ref):
    # NOTE soon to be not used
    passed, regions = check_ref(regions_ref, "Regions")
    if not passed:
        return JsonResponse(regions)

    if not DEBUG:
        credentials(f"{SAS_APP_URL}/", SAS_USERNAME, SAS_PASSWORD)

    # _, all_annotations = formatted_annotations(regions)
    # all_regions = [
    #     (canvas_nb, coord, img_file)
    #     for canvas_nb, coord, img_file in all_annotations
    #     if coord
    # ]
    all_regions = get_regions_annotations(regions)

    urls_list = []
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


def rgpd(request):
    return render(request, "rgpd.html")


def legacy_manifest(request, old_id):
    if not os.path.isfile(f"{MEDIA_DIR}/manifest/{old_id}.json"):
        return JsonResponse({})
    with open(f"{MEDIA_DIR}/manifest/{old_id}.json", "r") as manifest:
        return JsonResponse(json.loads(manifest.read()))


@login_required(login_url=f"/{APP_NAME}-admin/login/")
def advanced_search(request):
    # NOTE soon to be not used
    witness_list = Witness.objects.order_by("id")
    witness_filter = WitnessFilter(request.GET, queryset=witness_list)

    paginator = Paginator(witness_filter.qs, 3)  # 3 items per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "title": "Advanced search" if APP_LANG == "en" else "Recherche avancée",
        "witness_filter": witness_filter,
        "result_count": witness_filter.qs.count(),
        "page_obj": page_obj,  # witnesses
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


class DocumentSetAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return DocumentSet.objects.none()

        qs = DocumentSet.objects.all()
        qs = qs.filter(user=self.request.user).all()

        if self.q:
            qs = qs.filter(title__icontains=self.q)

        return qs


@csrf_exempt
def api_progress(request):
    """
    Receives treatment updates from API
    """
    if request.method == "POST":
        treatment_id = request.POST["experiment_id"]
        info = request.POST["message"]

        treatment = Treatment.objects.get(id=treatment_id)
        treatment.receive_notification(event=request.POST["event"], info=info)
        return JsonResponse({"message": "Update received"}, status=200)

    return JsonResponse({"message": "Invalid request"}, status=400)


@csrf_exempt
def cancel_treatment(request):
    """
    Cancel treatment in the API
    """
    import json

    data = json.loads(request.body)
    treatment_id = data.get("treatment_id")

    if not treatment_id:
        return JsonResponse({"error": "Invalid treatment ID"}, status=400)
    try:
        treatment = Treatment.objects.get(id=treatment_id)

        try:
            requests.post(url=f"{CV_API_URL}/{treatment.api_tracking_id}/cancel")
        except Exception as e:
            return JsonResponse({"error": "Could not connect to API"}, e)

        treatment.is_finished = True
        treatment.status = "CANCELLED"
        treatment.save()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": "Treatment not found"}, e)
