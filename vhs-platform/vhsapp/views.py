import csv
import json
import os
from urllib.request import urlopen
from urllib.parse import urlencode

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from iiif_prezi.factory import ManifestFactory, StructuralError

from django.contrib.auth.decorators import login_required
from vhs.settings import ENV

from vhsapp.models.witness import Volume, Manuscript
from vhsapp.models.constants import MS, VOL, MS_ABBR, VOL_ABBR
from vhs.settings import VHS_APP_URL, CANTALOUPE_APP_URL, SAS_APP_URL
from vhsapp.utils.functions import credentials, console, log
from vhsapp.utils.constants import (
    APP_NAME,
    APP_NAME_UPPER,
    APP_DESCRIPTION,
)
from vhsapp.utils.iiif import annotate_canvas, process_images, manifest_witness
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
    manifest = manifest_witness(id, MS_ABBR, version)
    try:
        return JsonResponse(manifest.toJSON(top=True))
    except StructuralError as e:
        log(
            f"[manifest_manuscript] Unable to create manifest for manuscript n°{id} (probably no images):\n{e}"
        )
        return JsonResponse(
            {
                "error": "Unable to create a valid manifest",
                "reason": f"Unable to create manifest for resource {id} (probably no image): {e}",
            }
        )


def manifest_volume(request, id, version):
    """
    Build a volume manifest using iiif-prezi library
    IIIF Presentation API 2.0
    """
    manifest = manifest_witness(id, VOL_ABBR, version)

    try:
        return JsonResponse(manifest.toJSON(top=True))
    except StructuralError as e:
        log(
            f"[manifest_volume] Unable to create manifest for volume n°{id} (probably no images):\n{e}"
        )
        return JsonResponse(
            {
                "error": "Unable to create a valid manifest",
                "reason": f"Unable to create manifest for resource {id} (probably no image):{e}",
            }
        )


def get_annotations(wit_id, annotations_path):
    try:
        with open(f"{BASE_DIR}/{MEDIA_PATH}/{annotations_path}/{wit_id}.txt") as f:
            return [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        return None


def annotation_auto(request, id, work):
    response = HttpResponse(content_type="text/csv")
    response[
        "Content-Disposition"
    ] = f"attachment; filename=annotations_iiif_{work}_{id}.csv"
    writer = csv.writer(response)
    writer.writerow(["IIIF_Image_Annotations"])
    annotations_path = VOL_ANNO_PATH if work == VOL else MS_ANNO_PATH

    lines = get_annotations(id, annotations_path)
    if lines is None:
        log(f"[annotation_auto] no annotation file for {work} n°{id}")
        writer.writerow([f"No annotation were generated for {work} n°{id}"])
        return response

    img_name = f"{work}{id}_0000.jpg"
    for line in lines:
        if len(line.split()) == 2:
            img_name = line.split()[1]
        else:
            region = f"{line.split()[0]},{line.split()[1]},{line.split()[2]},{line.split()[3]}"
            writer.writerow(
                [f"{CANTALOUPE_APP_URL}/iiif/2/{img_name}/{region}/full/0/default.jpg"]
            )

    return response


def annotate_work(request, id, version, work, work_abbr, canvas):
    annotations_path = VOL_ANNO_PATH if work == VOL else MS_ANNO_PATH

    lines = get_annotations(id, annotations_path)
    if lines is None:
        log(f"[annotate_work] no annotation file for {work} n°{id}")
        return JsonResponse({"@type": "sc:AnnotationList", "resources": []})

    nbr_anno = 0
    list_anno = []
    check = False
    for line in lines:
        if len(line.split()) == 2 and line.split()[0] == str(canvas):
            check = True
            continue
        if check:
            if len(line.split()) == 4:
                nbr_anno += 1
                list_anno.append(tuple(int(item) for item in tuple(line.split())))
            else:
                break
    return JsonResponse(
        {
            "@type": "sc:AnnotationList",
            "resources": [
                annotate_canvas(
                    id,
                    version,
                    work,
                    work_abbr,
                    canvas,
                    list_anno[num_anno],
                    num_anno,
                )
                for num_anno in range(nbr_anno)
                if nbr_anno > 0
            ],
        }
    )


def populate_annotation(request, id, work):  # TODO factorize with show work
    """
    Populate annotation store from IIIF Annotation List
    """
    work_abbr = VOL_ABBR if work == VOL else MS_ABBR
    annotations_path = VOL_ANNO_PATH if work == VOL else MS_ANNO_PATH

    if not ENV("DEBUG"):
        credentials(f"{SAS_APP_URL}/", ENV("SAS_USERNAME"), ENV("SAS_PASSWORD"))

    lines = get_annotations(id, annotations_path)
    if lines is None:
        log(f"[populate_annotation] no annotation file for {work} n°{id}")
        return HttpResponse(status=500)

    canvas = [line.split()[0] for line in lines if len(line.split()) == 2]
    iiif_url = f"{VHS_APP_URL}/{APP_NAME}/iiif/v2/{work}/{work_abbr}-{id}"

    for c in canvas:
        url_search = f"{SAS_APP_URL}/annotation/search?uri={iiif_url}/canvas/c{c}.json"
        # Store the response of URL
        response = urlopen(url_search)
        # Store the JSON response from url in data
        data = json.loads(response.read())
        if len(data) > 0:
            return HttpResponse(status=200)

    url_populate = f"{SAS_APP_URL}/annotation/populate"
    for line in lines:
        if len(line.split()) == 2:
            canvas = line.split()[0]
            params = {"uri": f"{iiif_url}/list/anno-{canvas}.json"}
            query_string = urlencode(params)
            data = query_string.encode("ascii")
            response = urlopen(url_populate, data)  # This will make the method "POST"

    return HttpResponse(status=200)


@login_required(login_url=f"/{APP_NAME}-admin/")
def show_work(request, id, work):
    work_model = Volume if work == VOL else Manuscript
    work_abbr = VOL_ABBR if work == VOL else MS_ABBR
    annotations_path = VOL_ANNO_PATH if work == VOL else MS_ANNO_PATH

    if not ENV("DEBUG"):
        credentials(f"{SAS_APP_URL}/", ENV("SAS_USERNAME"), ENV("SAS_PASSWORD"))

    lines = get_annotations(id, annotations_path)
    if lines is None:
        log(f"[show_work] no annotation file for {work} n°{id}")
        return JsonResponse({"error": "the annotations were not yet generated"})

    work_obj = get_object_or_404(work_model, pk=id)
    iiif_url = f"{VHS_APP_URL}/{APP_NAME}/iiif/v2/{work}/{work_abbr}-{id}"
    canvas_annos = []
    # TODO: do we need to load again all the annotations everytime?
    # TOOD: maybe loop on images of the manifest?
    for line in lines:
        # if the current line concerns an img (ie: line = "img_nb img_file.jpg")
        if len(line.split()) == 2:
            # Store the response of URL
            img_nb, img_file = line.split()
            iiif_img = f"{CANTALOUPE_APP_URL}/iiif/2/{img_file}/full/full/0/default.jpg"
            try:
                response = urlopen(
                    f"{SAS_APP_URL}/annotation/search?uri={iiif_url}/canvas/c{img_nb}.json"
                )
            except Exception as e:
                log(
                    f"[show_work]: Unable to retrieve annotation for {img_file}, annotation {img_nb}\n{e}"
                )
                return JsonResponse(
                    {
                        "error": f"unable to retrieve annotation for {iiif_img}",
                        "source": f"{SAS_APP_URL}/annotation/search?uri={iiif_url}/canvas/c{img_nb}.json",
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
            canvas_annos.append((annos, iiif_img))

    paginator = Paginator(canvas_annos, 10)
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
            "work": work,
            "work_obj": work_obj,
            "page_annos": page_annos,
            "url_manifest": f"{iiif_url}/manifest.json",
        },
    )
