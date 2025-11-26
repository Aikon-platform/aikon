import json
import os

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test

from app.webapp.models.regions import Regions
from app.config.settings import (
    SAS_APP_URL,
    DEBUG,
    SAS_USERNAME,
    LOGIN_URL,
)
from app.webapp.models.witness import Witness
from app.webapp.utils.functions import (
    credentials,
    list_to_txt,
    cls,
    delete_files,
    zip_img,
    get_files_with_prefix,
)
from app.webapp.utils.logger import log
from app.webapp.utils.iiif.annotation import (
    format_canvas_annotations,
    index_regions,
    destroy_regions,
    process_regions,
    formatted_annotations,
    reindex_file,
    get_regions_urls,
)
from app.webapp.utils.regions import (
    get_regions_img,
    create_empty_regions,
)
from app.webapp.utils.paths import REGIONS_PATH
from app.webapp.views import check_ref


def is_superuser(user):
    return user.is_superuser


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
            destroy_regions(regions)
        except Exception as e:
            return JsonResponse(
                {"error": f"Failed to delete regions #{regions.id}: {e}"}
            )

    digit = regions.get_digit() if regions else obj
    if not digit:
        return JsonResponse(
            {"error": f"Failed to retrieve digitization for regions #{obj_ref}"}
        )

    if anno_file := regions.region_file():
        try:
            with open(anno_file, "r") as file:
                process_regions(file.read(), digit)
            delete_files(anno_file)

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
            destroy_regions(regions)
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


def canvas_annotations(request, version, regions_ref, canvas_nb):
    regions_id = regions_ref.split("_")[-1].replace("anno", "")
    regions = get_object_or_404(Regions, pk=regions_id)
    return JsonResponse(format_canvas_annotations(regions, canvas_nb))


def populate_annotation(request, regions_id):
    """
    Populate annotation store from IIIF Annotation List
    """
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


@login_required(login_url=LOGIN_URL)
def export_selected_regions(request):
    urls_list = json.loads(request.POST.get("listeURL"))
    return zip_img(urls_list)
