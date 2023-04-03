import csv
import json
import os
from urllib.request import urlopen
from urllib.parse import urlencode

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
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
        log(f"Unable to create manifest for resource {id} (probably no images):\n{e}")
        return JsonResponse(
            {
                "error": "Unable to create a valid manifest",
                "reason": f"Unable to create manifest for resource {id} (probably no image):\n{e}",
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
        log(f"Unable to create manifest for resource {id} (probably no images):\n{e}")
        return JsonResponse(
            {
                "error": "Unable to create a valid manifest",
                "reason": f"Unable to create manifest for resource {id} (probably no image):\n{e}",
            }
        )


def annotation_auto(request, id, work):
    response = HttpResponse(content_type="text/csv")
    response[
        "Content-Disposition"
    ] = f"attachment; filename=annotations_iiif_{work}_{id}.csv"
    writer = csv.writer(response)
    writer.writerow(["IIIF_Image_Annotations"])
    annotations_path = VOL_ANNO_PATH if work == VOL else MS_ANNO_PATH

    # try:
    with open(f"{BASE_DIR}/{MEDIA_PATH}/{annotations_path}/{id}.txt") as f:
        lines = [line.strip() for line in f.readlines()]
        for line in lines:
            if len(line.split()) == 2:
                img_name = line.split()[1]
            else:
                region = f"{line.split()[0]},{line.split()[1]},{line.split()[2]},{line.split()[3]}"
                writer.writerow(
                    [
                        f"{CANTALOUPE_APP_URL}/iiif/2/{img_name}/{region}/full/0/default.jpg"
                    ]
                )
    # except FileNotFoundError:
    #     # TODO do something when there is no file
    #     print("")
    return response


def annotate_work(request, id, version, work, work_abbr, canvas):
    annotations_path = VOL_ANNO_PATH if work == VOL else MS_ANNO_PATH
    try:
        with open(f"{BASE_DIR}/{MEDIA_PATH}/{annotations_path}/{id}.txt") as f:
            lines = [line.strip() for line in f.readlines()]
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
                        list_anno.append(
                            tuple(int(item) for item in tuple(line.split()))
                        )
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
    except FileNotFoundError:
        return JsonResponse(
            {
                "@type": "sc:AnnotationList",
                "resources": [],
            }
        )


def populate_annotation(request, id, work):  # TODO factorize with show work
    """
    Populate annotation store from IIIF Annotation List
    """
    work_map = {
        VOL: (VOL_ABBR, VOL_ANNO_PATH),
        MS: (MS_ABBR, MS_ANNO_PATH),
    }
    work_abbr, annotations_path = work_map.get(work, (None, None))
    if not ENV("DEBUG"):
        credentials(f"{SAS_APP_URL}/", ENV("SAS_USERNAME"), ENV("SAS_PASSWORD"))
    with open(f"{BASE_DIR}/{MEDIA_PATH}/{annotations_path}/{id}.txt") as f:
        lines = [line.strip() for line in f.readlines()]
    canvas = [line.split()[0] for line in lines if len(line.split()) == 2]
    for c in canvas:
        url_search = f"{SAS_APP_URL}/annotation/search?uri={VHS_APP_URL}/{APP_NAME}/iiif/v2/{work}/{work_abbr}-{id}/canvas/c{c}.json"
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
            params = {
                "uri": f"{VHS_APP_URL}/{APP_NAME}/iiif/v2/{work}/{work_abbr}-{id}/list/anno-{canvas}.json"
            }
            query_string = urlencode(params)
            data = query_string.encode("ascii")
            response = urlopen(url_populate, data)  # This will make the method "POST"

    return HttpResponse(status=200)


@login_required(login_url=f"/{APP_NAME}-admin/")
def show_work(request, id, work):
    work_map = {
        MS: (Manuscript, MS_ABBR, MS_ANNO_PATH),
        VOL: (Volume, VOL_ABBR, VOL_ANNO_PATH),
    }
    work_model, work_abbr, annotations_path = work_map.get(work, (None, None, None))
    work_obj = get_object_or_404(work_model, pk=id)
    url_iiif = f"{VHS_APP_URL}/{APP_NAME}/iiif/v2/{work}/{work_abbr}-{id}"
    canvas_annos = []
    if not ENV("DEBUG"):
        credentials(f"{SAS_APP_URL}/", ENV("SAS_USERNAME"), ENV("SAS_PASSWORD"))

    anno_file = f"{BASE_DIR}/{MEDIA_PATH}/{annotations_path}/{id}.txt"
    if not os.path.exists(anno_file):
        return JsonResponse({"error": "the annotations were not yet generated"})

    with open(anno_file) as f:
        lines = [line.strip() for line in f.readlines()]
        for line in lines:
            # if the current line concerns an img (ie: line = "img_nb img_file.jpg")
            if len(line.split()) == 2:
                # Store the response of URL
                img_nb, img_file = line.split()
                iiif_img = (
                    f"{CANTALOUPE_APP_URL}/iiif/2/{img_file}/full/full/0/default.jpg"
                )
                try:
                    response = urlopen(
                        f"{SAS_APP_URL}/annotation/search?uri={url_iiif}/canvas/c{img_nb}.json"
                    )
                except Exception as e:
                    log(e)
                    return JsonResponse(
                        {
                            "error": f"unable to retrieve annotation for {iiif_img}",
                            "source": f"{SAS_APP_URL}/annotation/search?uri={url_iiif}/canvas/c{img_nb}.json",
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
    return render(
        request,
        "vhsapp/show.html",
        context={
            "work": work,
            "work_obj": work_obj,
            "canvas_annos": canvas_annos,
            "url_manifest": f"{url_iiif}/manifest.json",
        },
    )
