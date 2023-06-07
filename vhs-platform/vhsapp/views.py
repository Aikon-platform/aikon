import csv
import json
import os
import re
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
from vhsapp.utils.iiif.iiif_process import (
    annotate_canvas,
    process_images,
    manifest_witness,
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
    try:
        manifest = manifest_witness(id, MS_ABBR, version)
    except Exception as e:
        return JsonResponse(
            {
                "error": "Unable to create a valid manifest",
                "reason": f"Unable to create manifest for resource {id} (probably no manuscript): {e}",
            }
        )

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


def annotation_auto(request, id, witness):
    response = HttpResponse(content_type="text/csv")
    response[
        "Content-Disposition"
    ] = f"attachment; filename=annotations_iiif_{witness}_{id}.csv"
    writer = csv.writer(response)
    writer.writerow(["IIIF_Image_Annotations"])
    annotations_path = VOL_ANNO_PATH if witness == VOL else MS_ANNO_PATH

    lines = get_annotations(id, annotations_path)
    if lines is None:
        log(f"[annotation_auto] no annotation file for {witness} n°{id}")
        writer.writerow([f"No annotation were generated for {witness} n°{id}"])
        return response

    img_name = f"{witness}{id}_0000.jpg"
    for line in lines:
        if len(line.split()) == 2:
            img_name = line.split()[1]
        else:
            region = f"{line.split()[0]},{line.split()[1]},{line.split()[2]},{line.split()[3]}"
            writer.writerow(
                [f"{CANTALOUPE_APP_URL}/iiif/2/{img_name}/{region}/full/0/default.jpg"]
            )

    return response


def annotate_witness(request, id, version, witness, wit_abbr, canvas):
    annotations_path = VOL_ANNO_PATH if witness == VOL else MS_ANNO_PATH

    lines = get_annotations(id, annotations_path)
    if lines is None:
        log(f"[annotate_witness] no annotation file for {witness} n°{id}")
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
                    witness,
                    wit_abbr,
                    canvas,
                    list_anno[num_anno],
                    num_anno,
                )
                for num_anno in range(nbr_anno)
                if nbr_anno > 0
            ],
        }
    )


def populate_annotation(request, id, witness):
    """
    Populate annotation store from IIIF Annotation List
    """
    wit_abbr = VOL_ABBR if witness == VOL else MS_ABBR
    annotations_path = VOL_ANNO_PATH if witness == VOL else MS_ANNO_PATH

    if not ENV("DEBUG"):
        credentials(f"{SAS_APP_URL}/", ENV("SAS_USERNAME"), ENV("SAS_PASSWORD"))

    lines = get_annotations(id, annotations_path)
    if lines is None:
        log(f"[populate_annotation] no annotation file for {witness} n°{id}")
        return HttpResponse(status=500)

    annotated_canvases = {}
    current_canvas = "0"
    for line in lines:
        # if the current line concerns an img (ie: line = "img_nb img_file.jpg")
        if len(line.split()) == 2:
            current_canvas = str(line.split()[0])
            annotated_canvases[current_canvas] = 0
        else:
            if current_canvas in annotated_canvases:
                annotated_canvases[current_canvas] += 1

    iiif_url = f"{VHS_APP_URL}/{APP_NAME}/iiif/v2/{witness}/{wit_abbr}-{id}"

    for c in annotated_canvases:
        # check if annotations are already indexed
        detected_anno = annotated_canvases[c]
        response = urlopen(
            f"{SAS_APP_URL}/annotation/search?uri={iiif_url}/canvas/c{c}.json"
        )
        indexed_anno = json.loads(response.read())

        # if the canvas has not the same nb of annotations as in the content of the annotation text file
        if len(indexed_anno) != detected_anno:
            # TODO here, if there is not the same number, all annotations are reindexed, causing possibly duplicates
            # {iiif_url}/list/anno-{c}.json is calling annotate_witness(), thus indexing annotations for each canvas
            params = urlencode({"uri": f"{iiif_url}/list/anno-{c}.json"}).encode(
                "ascii"
            )
            urlopen(f"{SAS_APP_URL}/annotation/populate", params)

    return HttpResponse(status=200)


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

    lines = get_annotations(id, annotations_path)
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
