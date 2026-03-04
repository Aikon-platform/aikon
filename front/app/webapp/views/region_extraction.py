import json
import os

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test

from app.webapp.models.region_extraction import RegionExtraction
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
    destroy_region_extraction,
    process_region_extraction,
    formatted_annotations,
    reindex_file,
    get_regions_urls,
)
from app.webapp.utils.region_extraction import (
    get_region_extraction_img,
    create_empty_region_extraction,
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
    either to create a RegionExtraction obj from a regions txt file if obj_ref is a digit_ref
    or to delete then create a new regions file if obj_ref is a region_extraction_ref
    TODO differenciate clearly from index_regions
    """
    passed, obj = check_ref(obj_ref, "RegionExtraction")
    if not passed:
        return JsonResponse(obj)

    region_extraction = obj if cls(obj) == RegionExtraction else None
    if region_extraction:
        try:
            destroy_region_extraction(region_extraction)
        except Exception as e:
            return JsonResponse(
                {
                    "error": f"Failed to delete region extraction #{region_extraction.id}: {e}"
                }
            )

    digit = region_extraction.get_digit() if region_extraction else obj
    if not digit:
        return JsonResponse(
            {
                "error": f"Failed to retrieve digitization for region extraction #{obj_ref}"
            }
        )

    if anno_file := region_extraction.region_file():
        try:
            with open(anno_file, "r") as file:
                process_region_extraction(file.read(), digit)
            delete_files(anno_file)

            return JsonResponse({"message": "Regions were re-indexed."})

        except Exception as e:
            return JsonResponse(
                {"error": f"Failed to index regions for digit #{digit.id}: {e}"}
            )
    else:
        create_empty_region_extraction(digit)

    return JsonResponse({"error": f"No regions file for reference #{obj_ref}."})


@user_passes_test(is_superuser)
def index_witness_regions(request, wit_id):
    wit = get_object_or_404(Witness, pk=wit_id)
    region_extraction_files = sorted(
        get_files_with_prefix(REGIONS_PATH, f"{wit.get_ref()}_")
    )
    res = {
        "All": region_extraction_files,
        "Indexed": [],
        "Not indexed": [],
    }
    for file in region_extraction_files:
        passed, a_ref = reindex_file(file)
        res["Indexed" if passed else "Not indexed"].append(a_ref)

    return JsonResponse(res)


@user_passes_test(is_superuser)
def index_regions(request, region_extraction_ref=None):
    """
    Index the content of a regions txt file named after the region_extraction_ref (wit<id>_<digit><id>_anno<id>.txt) into SAS
    without creating an annotation record if one is already existing
    If no region_extraction_ref is provided all regions files for mediafiles/regions are indexed
    """
    region_extraction_files = (
        os.listdir(REGIONS_PATH)
        if not region_extraction_ref
        else [region_extraction_ref]
    )

    res = {
        "All": region_extraction_files,
        "Indexed": [],
        "Not indexed": [],
    }

    for file in region_extraction_files:
        passed, a_ref = reindex_file(file)
        res["Indexed" if passed else "Not indexed"].append(a_ref)

    return JsonResponse(res)


@user_passes_test(is_superuser)
def delete_annotations_regions(request, obj_ref):
    """
    Unindex SAS annotations + delete RegionExtraction record from the database
    """
    passed, obj = check_ref(obj_ref, "RegionExtraction")
    if not passed:
        return JsonResponse(obj)

    region_extraction = obj if cls(obj) == RegionExtraction else None
    if region_extraction:
        try:
            destroy_region_extraction(region_extraction)
        except Exception as e:
            return JsonResponse(
                {
                    "error": f"Failed to delete region extraction file and annotations for reference #{region_extraction.id}: {e}"
                }
            )

    return JsonResponse(
        {"error": f"No region extraction file for reference #{obj_ref}."}
    )


def get_regions_img_list(request, region_extraction_ref):
    """
    return something like that
    {
        "wit1_man191_0009_166,1325,578,516": ""https://eida.obspm.fr/iiif/2/wit1_man191_0009.jpg/166,1325,578,516/full/0/default.jpg"",
        "wit1_man191_0027_1143,2063,269,245": "https://eida.obspm.fr/iiif/2/wit1_man191_0027.jpg/1143,2063,269,245/full/0/default.jpg",
        "wit1_man191_0031_857,2013,543,341": "https://eida.obspm.fr/iiif/2/wit1_man191_0031.jpg/857,2013,543,341/full/0/default.jpg",
        "img_name": "..."
    }
    """
    passed, region_extraction = check_ref(region_extraction_ref, "RegionExtraction")
    if not passed:
        return JsonResponse(region_extraction)

    try:
        regions_dict = get_regions_urls(region_extraction)
    except Exception as e:
        error = f"[get_regions_img_list] Couldn't generate list of region images for {region_extraction_ref}"
        log(error, e)
        return JsonResponse({"response": error, "reason": e}, safe=False)

    return JsonResponse(regions_dict, status=200, safe=False)


def export_region_extraction_img(request, region_extraction_id):
    regions = get_object_or_404(RegionExtraction, pk=region_extraction_id)
    images = get_region_extraction_img(regions)
    return list_to_txt(images, regions.get_ref())


def canvas_annotations(request, version, region_extraction_ref, canvas_nb):
    region_extraction_id = region_extraction_ref.split("_")[-1].replace("anno", "")
    region_extraction = get_object_or_404(RegionExtraction, pk=region_extraction_id)
    return JsonResponse(format_canvas_annotations(region_extraction, canvas_nb))


def populate_annotation(request, region_extraction_id):
    """
    Populate annotation store from IIIF Annotation List
    """
    region_extraction = get_object_or_404(RegionExtraction, pk=region_extraction_id)
    return HttpResponse(status=200 if index_regions(region_extraction) else 500)


def validate_region_extraction(request, region_extraction_ref):
    """
    Validate the manually corrected region extraction
    """
    try:
        passed, region_extraction = check_ref(region_extraction_ref, "RegionExtraction")
        if not passed:
            return HttpResponse(region_extraction, status=500)
        region_extraction.is_validated = True
        region_extraction.save()
        return HttpResponse(status=200)
    except Exception as e:
        return HttpResponse(f"An error occurred: {e}", status=500)


def witness_sas_annotations(request, region_extraction_id):
    regions = get_object_or_404(RegionExtraction, pk=region_extraction_id)
    _, c_annos = formatted_annotations(regions)
    return JsonResponse(c_annos, safe=False)


@login_required(login_url=LOGIN_URL)
def export_selected_regions(request):
    urls_list = json.loads(request.POST.get("listeURL"))
    return zip_img(urls_list)
