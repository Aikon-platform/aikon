import csv
import json
import os
import re
from urllib.request import urlopen
from urllib.parse import urlencode

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from django.contrib.auth.decorators import login_required
from vhs.settings import ENV

from vhsapp.models.witness import Volume, Manuscript
from vhsapp.models.constants import MS, VOL, MS_ABBR, VOL_ABBR
from vhs.settings import VHS_APP_URL, CANTALOUPE_APP_URL, SAS_APP_URL
from vhsapp.utils.functions import credentials, console, log, list_to_txt
from vhsapp.utils.constants import (
    APP_NAME,
    APP_NAME_UPPER,
    APP_DESCRIPTION,
)
from vhsapp.utils.iiif.manifest import (
    process_images,
    manifest_wit_type,
)
from vhsapp.utils.iiif.annotation import (
    get_txt_annos,
    format_canvas_annos,
    check_wit_annotation,
    get_anno_img,
)
from vhsapp.utils.paths import (
    MEDIA_PATH,
    VOL_ANNO_PATH,
    MS_ANNO_PATH,
    BASE_DIR,
    IMG_PATH,
)


def admin_vhs(request):
    return redirect("admin:index")


def manifest_manuscript(request, id, version):
    """
    Build a manuscript manifest using iiif-prezi library
    IIIF Presentation API 2.0
    """
    return JsonResponse(manifest_wit_type(id, MS, version))


def manifest_volume(request, id, version):
    """
    Build a volume manifest using iiif-prezi library
    IIIF Presentation API 2.0
    """
    return JsonResponse(manifest_wit_type(id, VOL, version))


def export_anno_img(request, id, wit_type):
    annotations = get_anno_img(id, wit_type)
    return list_to_txt(annotations, f"{wit_type}#{id}_ annotations")


def canvas_annotations(request, id, version, wit_type, wit_abbr, canvas):
    return JsonResponse(format_canvas_annos(id, version, wit_type, wit_abbr, canvas))


def populate_annotation(request, id, wit_type):
    """
    Populate annotation store from IIIF Annotation List
    """
    if not ENV("DEBUG"):
        credentials(f"{SAS_APP_URL}/", ENV("SAS_USERNAME"), ENV("SAS_PASSWORD"))

    return HttpResponse(status=200 if check_wit_annotation(id, wit_type) else 500)


def get_img_prefix(obj, wit=MS, wit_abbr=MS_ABBR):
    img_prefix = f"{wit_abbr}{obj.id}"
    if hasattr(obj, f"pdf{wit}_set"):
        if getattr(obj, f"pdf{wit}_set").first():
            img_prefix = (
                obj.pdfmanuscript_set.first().pdf.name.split("/")[-1].split(".")[0]
            )
    return img_prefix


def get_imgs(wit_prefix):
    # TODO make a method of Witness class out of this function
    pattern = re.compile(rf"{wit_prefix}_\d{{4}}\.jpg", re.IGNORECASE)
    wit_imgs = []

    for img in os.listdir(f"{BASE_DIR}/{IMG_PATH}"):
        if pattern.match(img):
            wit_imgs.append(img)

    return wit_imgs


@login_required(login_url=f"/{APP_NAME}-admin/")
def show_witness(request, id, wit):
    wit_model = Volume if wit == VOL else Manuscript
    wit_abbr = VOL_ABBR if wit == VOL else MS_ABBR
    annotations_path = VOL_ANNO_PATH if wit == VOL else MS_ANNO_PATH

    if not ENV("DEBUG"):
        credentials(f"{SAS_APP_URL}/", ENV("SAS_USERNAME"), ENV("SAS_PASSWORD"))

    lines = get_txt_annos(id, annotations_path)
    if lines is None:
        log(f"[show_wit] no annotation file for {wit} n°{id}")
        return JsonResponse({"error": "the annotations were not yet generated"})

    wit_obj = get_object_or_404(wit_model, pk=id)
    iiif_url = f"{VHS_APP_URL}/{APP_NAME}/iiif/v2/{wit}/{wit_abbr}-{id}"

    wit_imgs = get_imgs(get_img_prefix(wit_obj, wit, wit_abbr))
    canvas_annos = []
    bboxes = []
    # TODO: do we need to load again all the annotations everytime?
    # TODO: maybe loop on images of the manifest?

    # TODO displace in annotation.py and create get_witness_annos()
    for line in lines:
        # if the current line concerns an img (ie: line = "img_nb img_file.jpg")
        if len(line.split()) == 2:
            # Store the response of URL
            canvas_nb, img_file = line.split()

            if img_file not in wit_imgs:
                # log(f"[show_wit]: Missing img {img_file}")
                continue

            img_url = f"{CANTALOUPE_APP_URL}/iiif/2/{img_file}/full/full/0/default.jpg"
            try:
                response = urlopen(
                    f"{SAS_APP_URL}/annotation/search?uri={iiif_url}/canvas/c{canvas_nb}.json"
                )
            except Exception as e:
                log(
                    f"[show_wit]: Unable to retrieve annotation for {img_file}, annotation {canvas_nb}\n{e}"
                )
                return JsonResponse(
                    {
                        "error": f"unable to retrieve annotation for {img_url}",
                        "source": f"{SAS_APP_URL}/annotation/search?uri={iiif_url}/canvas/c{canvas_nb}.json",
                    }
                )
            # Store the JSON response from url in data
            data = json.loads(response.read())
            annos = [
                (
                    (d["on"][0]["selector"]["default"]["value"]).split("=")[1],
                    d["@id"].split("/")[-1],
                )
                for d in data
                if len(data) > 0
            ]
            bbox_ids = [str(d["@id"].split("/")[-1]) for d in data if len(data) > 0]
            bboxes.extend(bbox_ids)
            canvas_annos.append((canvas_nb, annos, img_file))

    paginator = Paginator(canvas_annos, 50)
    try:
        page_annos = paginator.page(request.GET.get("page"))
    except PageNotAnInteger:
        page_annos = paginator.page(1)
    except EmptyPage:
        page_annos = paginator.page(paginator.num_pages)

    return render(
        request,
        "vhsapp/show.html",
        context={
            "wit": wit,
            "wit_obj": wit_obj,
            "page_annos": page_annos,
            "bboxes": json.dumps(bboxes),
            "url_manifest": f"{iiif_url}/manifest.json",
        },
    )


# TODO: create test to find integrity of a manuscript:
#  if it has the correct number of images, if all its images are img files
#  if annotations were correctly defined (same img name in file that images on server)
