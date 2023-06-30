import json
import requests
from dal import autocomplete

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from django.contrib.auth.decorators import login_required

from app.webapp.models.OLD.witness import Volume, Manuscript
from app.webapp.models.utils.constants import MS, VOL, MS_ABBR, VOL_ABBR
from app.config.settings import (
    APP_URL,
    CANTALOUPE_APP_URL,
    SAS_APP_URL,
    APP_NAME,
    ENV,
    GEONAMES_USER,
)
from app.webapp.utils.functions import credentials, list_to_txt
from app.webapp.utils.logger import console, log
from app.webapp.utils.iiif.manifest import manifest_wit_type
from app.webapp.utils.iiif.annotation import (
    format_canvas_annos,
    check_wit_annotation,
    get_anno_img,
    formatted_wit_anno,
    get_canvas_list,
    get_indexed_canvas_annos,
)


def admin_app(request):
    return redirect("admin:index")


def manifest_manuscript(request, wit_id, version):
    """
    Build a manuscript manifest using iiif-prezi library IIIF Presentation API 2.0
    """
    return JsonResponse(manifest_wit_type(wit_id, MS, version))


def manifest_volume(request, wit_id, version):
    """
    Build a volume manifest using iiif-prezi library IIIF Presentation API 2.0
    """
    return JsonResponse(manifest_wit_type(wit_id, VOL, version))


def export_anno_img(request, wit_id, wit_type):
    annotations = get_anno_img(wit_id, wit_type)
    return list_to_txt(annotations, f"{wit_type}#{wit_id}_ annotations")


def canvas_annotations(request, wit_id, version, wit_type, canvas):
    return JsonResponse(format_canvas_annos(wit_id, version, wit_type, canvas))


def populate_annotation(request, wit_id, wit_type):
    """
    Populate annotation store from IIIF Annotation List
    """
    if not ENV("DEBUG"):
        credentials(f"{SAS_APP_URL}/", ENV("SAS_USERNAME"), ENV("SAS_PASSWORD"))

    return HttpResponse(status=200 if check_wit_annotation(wit_id, wit_type) else 500)


def validate_annotation(request, wit_id, wit_type):
    """
    Validate the manually corrected annotations
    """
    try:
        witness = get_object_or_404(
            Volume if wit_type == VOL else Manuscript, pk=wit_id
        )
        witness.manifest_final = True
        witness.save()
        return HttpResponse(status=200)
    except (Manuscript.DoesNotExist, Volume.DoesNotExist):
        return HttpResponse(f"{wit_type} #{wit_id} does not exist", status=500)
    except Exception as e:
        return HttpResponse(f"An error occurred: {e}", status=500)


def witness_sas_annotations(request, wit_id, wit_type):
    witness = get_object_or_404(Volume if wit_type == VOL else Manuscript, pk=wit_id)
    _, canvas_annos = formatted_wit_anno(witness, wit_type)
    return JsonResponse(canvas_annos, safe=False)


def test(request, wit_id, wit_type):
    return JsonResponse(
        {"response": f"Nothing to test for {wit_type} #{wit_id}"},
        safe=False,
    )


@login_required(login_url=f"/{APP_NAME}-admin/")
def show_witness(request, wit_id, wit_type):
    witness = get_object_or_404(Volume if wit_type == VOL else Manuscript, pk=wit_id)

    if not ENV("DEBUG"):
        credentials(f"{SAS_APP_URL}/", ENV("SAS_USERNAME"), ENV("SAS_PASSWORD"))

    bboxes, canvas_annos = formatted_wit_anno(witness, wit_type)

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
