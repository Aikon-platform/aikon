import csv
import json
import environ
from urllib.request import urlopen
from urllib.parse import urlencode
from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from vhs.settings import VHS_APP_URL, CANTALOUPE_APP_URL, SAS_APP_URL
from vhsapp.models import Manuscript, Volume
from vhsapp.utils.constants import (
    APP_NAME,
    APP_NAME_UPPER,
    MS,
    MS_ABBR,
    VOL,
    VOL_ABBR,
    APP_DESCRIPTION,
)
from vhsapp.utils.functions import credentials
from iiif_prezi.factory import ManifestFactory

from vhsapp.utils.iiif import annotate_canvas, process_images
from vhsapp.utils.paths import (
    MEDIA_PATH,
    VOL_ANNO_PATH,
    MS_ANNO_PATH,
)

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(env_file=str(BASE_DIR / "vhs" / ".env"))


def admin_vhs(request):
    return redirect("admin:index")


def manifest_manuscript(request, id, version):
    """
    Build a manuscript manifest using iiif-prezi library
    IIIF Presentation API 2.0
    """
    # Get the Manuscript object or return a 404 error if it doesn't exist
    manuscript = get_object_or_404(Manuscript, pk=id)
    # Configure the factory
    fac = ManifestFactory()
    fac.set_base_prezi_uri(f"{VHS_APP_URL}vhs/iiif/{version}/{MS}/{MS_ABBR}-{id}/")
    fac.set_base_image_uri(f"{CANTALOUPE_APP_URL}iiif/2/")
    fac.set_iiif_image_info(version="2.0", lvl="2")
    # Build the manifest
    mf = fac.manifest(ident="manifest", label=manuscript.work.title)
    mf.set_metadata(
        {
            "Author": manuscript.author.name,
            "Place of conservation": manuscript.conservation_place,
            "Reference number": manuscript.reference_number,
            "Date (century)": manuscript.date_century,
            "Sheet(s)": manuscript.sheets,
        }
    )
    if date_free := manuscript.date_free:
        mf.set_metadata({"Date": date_free})
    if origin_place := manuscript.origin_place:
        mf.set_metadata({"Place of origin": origin_place})
    if remarks := manuscript.remarks:
        mf.set_metadata({"Remarks": remarks})
    if copyists := manuscript.copyists:
        mf.set_metadata({"Copyist(s)": copyists})
    if miniaturists := manuscript.miniaturists:
        mf.set_metadata({"Miniaturist(s)": miniaturists})
    if digitized_version := manuscript.digitized_version:
        mf.set_metadata({"Source of the digitized version": digitized_version.source})
    if pinakes_link := manuscript.pinakes_link:
        mf.set_metadata(
            {"Link to Pinakes (greek mss) or Medium-IRHT (latin mss)": pinakes_link}
        )
    # Set the manifest's attribution, description, and viewing hint
    mf.attribution = f"{APP_NAME_UPPER} platform"
    mf.description = APP_DESCRIPTION
    mf.viewingHint = "individuals"
    # And walk through the pages
    seq = mf.sequence(ident="normal", label="Normal Order")
    process_images(manuscript, seq, version)
    data = mf.toJSON(top=True)

    return JsonResponse(data)


def manifest_volume(request, id, version):
    """
    Build a volume manifest using iiif-prezi library
    IIIF Presentation API 2.0
    """
    # Get the Volume object or return a 404 error if it doesn't exist
    volume = get_object_or_404(Volume, pk=id)
    # Configure the factory
    fac = ManifestFactory()
    fac.set_base_prezi_uri(f"{VHS_APP_URL}vhs/iiif/{version}/{VOL}/{VOL_ABBR}-{id}/")
    fac.set_base_image_uri(f"{CANTALOUPE_APP_URL}iiif/2/")
    fac.set_iiif_image_info(version="2.0", lvl="2")
    # Build the manifest
    mf = fac.manifest(ident="manifest", label=volume.title)
    mf.set_metadata(
        {
            "Author": volume.printed.author.name,
            "Number or identifier of volume": volume.number_identifier,
            "Place": volume.place,
            "Date": volume.date,
            "Publishers/booksellers": volume.publishers_booksellers,
            "Description of work": volume.printed.description,
        }
    )
    if descriptive_elements := volume.printed.descriptive_elements:
        mf.set_metadata({"Descriptive elements of the content": descriptive_elements})
    if illustrators := volume.printed.illustrators:
        mf.set_metadata({"Illustrator(s)": illustrators})
    if engravers := volume.printed.engravers:
        mf.set_metadata({"Engraver(s)": engravers})
    if digitized_version := volume.digitized_version:
        mf.set_metadata({"Source of the digitized version": digitized_version.source})
    if comment := volume.comment:
        mf.set_metadata({"Comment": comment})
    if other_copies := volume.other_copies:
        mf.set_metadata({"Other copy(ies)": other_copies})
    # Set the manifest's attribution, description and viewing hint
    mf.attribution = f"{APP_NAME_UPPER} platform"
    mf.description = APP_DESCRIPTION
    mf.viewingHint = "individuals"
    # And walk through the pages
    seq = mf.sequence(ident="normal", label="Normal Order")
    process_images(volume, seq, version)
    data = mf.toJSON(top=True)

    return JsonResponse(data)


def annotation_auto(request, id, work):
    response = HttpResponse(content_type="text/csv")
    response[
        "Content-Disposition"
    ] = f"attachment; filename=annotations_iiif_{work}_{id}.csv"
    writer = csv.writer(response)
    writer.writerow(["IIIF_Image_Annotations"])
    annotations_path = VOL_ANNO_PATH if work == VOL else MS_ANNO_PATH
    with open(f"{MEDIA_PATH}{annotations_path}{id}.txt") as f:
        lines = [line.strip() for line in f.readlines()]
        for line in lines:
            if len(line.split()) == 2:
                img_name = line.split()[1]
            else:
                region = f"{line.split()[0]},{line.split()[1]},{line.split()[2]},{line.split()[3]}"
                writer.writerow(
                    [
                        f"{CANTALOUPE_APP_URL}iiif/2/{img_name}/{region}/full/0/default.jpg"
                    ]
                )
    return response


def annotate_work(request, id, version, work, work_abbr, canvas):
    annotations_path = VOL_ANNO_PATH if work == VOL else MS_ANNO_PATH
    with open(f"{MEDIA_PATH}{annotations_path}{id}.txt") as f:
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
                    list_anno.append(tuple(int(item) for item in tuple(line.split())))
                else:
                    break
    data = {
        "@type": "sc:AnnotationList",
        "resources": [
            annotate_canvas(
                id, version, work, work_abbr, canvas, list_anno[num_anno], num_anno
            )
            for num_anno in range(nbr_anno)
            if nbr_anno > 0
        ],
    }
    return JsonResponse(data)


def populate_annotation(request, id, work):
    """
    Populate annotation store from IIIF Annotation List
    """
    work_map = {
        VOL: (VOL_ABBR, VOL_ANNO_PATH),
        MS: (MS_ABBR, MS_ANNO_PATH),
    }
    work_abbr, annotations_path = work_map.get(work, (None, None))
    if not env("DEBUG"):
        credentials(SAS_APP_URL, env("SAS_USERNAME"), env("SAS_PASSWORD"))
    with open(f"{MEDIA_PATH}{annotations_path}{id}.txt") as f:
        lines = [line.strip() for line in f.readlines()]
    canvas = [line.split()[0] for line in lines if len(line.split()) == 2]
    for c in canvas:
        url_search = f"{SAS_APP_URL}annotation/search?uri={VHS_APP_URL}vhs/iiif/v2/{work}/{work_abbr}-{id}/canvas/c{c}.json"
        # Store the response of URL
        response = urlopen(url_search)
        # Store the JSON response from url in data
        data = json.loads(response.read())
        if len(data) > 0:
            return HttpResponse(status=200)
    url_populate = f"{SAS_APP_URL}annotation/populate"
    for line in lines:
        if len(line.split()) == 2:
            canvas = line.split()[0]
            params = {
                "uri": f"{VHS_APP_URL}vhs/iiif/v2/{work}/{work_abbr}-{id}/list/anno-{canvas}.json"
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
    url_manifest = f"{VHS_APP_URL}vhs/iiif/v2/{work}/{work_abbr}-{id}/manifest.json"
    canvas_annos = []
    if not env("DEBUG"):
        credentials(SAS_APP_URL, env("SAS_USERNAME"), env("SAS_PASSWORD"))
    with open(f"{MEDIA_PATH}{annotations_path}{id}.txt") as f:
        lines = [line.strip() for line in f.readlines()]
        for line in lines:
            if len(line.split()) == 2:
                url_search = f"{SAS_APP_URL}annotation/search?uri={VHS_APP_URL}vhs/iiif/v2/{work}/{work_abbr}-{id}/canvas/c{line.split()[0]}.json"
                # Store the response of URL
                response = urlopen(url_search)
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
                canvas_annos.append(
                    (
                        annos,
                        f"{CANTALOUPE_APP_URL}iiif/2/{line.split()[1]}/full/full/0/default.jpg",
                    )
                )
    return render(
        request,
        "vhsapp/show.html",
        context={
            "work": work,
            "work_obj": work_obj,
            "canvas_annos": canvas_annos,
            "url_manifest": url_manifest,
        },
    )
