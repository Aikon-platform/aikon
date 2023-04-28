import os
import re

from datetime import datetime
from PIL import Image, UnidentifiedImageError
from django.shortcuts import get_object_or_404
from iiif_prezi.factory import ManifestFactory
from pikepdf import Pdf

from vhsapp.utils.constants import (
    APP_NAME,
    MANIFEST_AUTO,
    MANIFEST_V2,
    APP_NAME_UPPER,
    APP_DESCRIPTION,
)
from vhsapp.utils.paths import MEDIA_PATH, IMG_PATH, BASE_DIR
from vhsapp.models.constants import VOL_ABBR, MS_ABBR, VOL, MS
from vhs.settings import SAS_APP_URL, VHS_APP_URL, CANTALOUPE_APP_URL
from vhsapp.models.witness import Volume, Manuscript
from vhsapp.utils.logger import iiif_log, console, log


def process_images(work, seq, version):
    """
    Process the images of a work and add them to a sequence
    """
    if hasattr(work, "imagemanuscript_set"):  # Manuscripts
        imgs = work.imagemanuscript_set.all()
        pdf_first = work.pdfmanuscript_set.first()
        manifest_first = work.manifestmanuscript_set.first()
        work_abbr = MS_ABBR
    else:  # Volumes
        imgs = work.imagevolume_set.all()
        pdf_first = work.pdfvolume_set.first()
        manifest_first = work.manifestvolume_set.first()
        work_abbr = VOL_ABBR

    # Check type of scans that were uploaded
    if imgs:  # IMAGES
        for counter, img in enumerate(imgs, start=1):
            img_name = img.image.url.split("/")[-1]
            try:
                build_canvas_and_annotation(
                    seq, counter, img_name, Image.open(img.image), version
                )
            except UnidentifiedImageError as e:
                log(f"[process_images] Unable to retrieve {img_name}\n{e}")
            except FileNotFoundError as e:
                log(f"[process_images] Non existing {img_name}\n{e}")

    # Check if there is a PDF work and process it
    elif pdf_first:  # PDF
        # TODO: factorize with pdf_to_img() in functions.py
        # MARKER console(pdf_first.pdf)
        with Pdf.open(f"{BASE_DIR}/{MEDIA_PATH}/{pdf_first.pdf}") as pdf_file:
            for counter in range(1, len(pdf_file.pages) + 1):
                img_name = pdf_first.pdf.name.split("/")[-1].replace(
                    ".pdf", f"_{counter:04d}.jpg"
                )
                try:
                    build_canvas_and_annotation(
                        seq,
                        counter,
                        img_name,
                        Image.open(f"{BASE_DIR}/{IMG_PATH}/{img_name}"),
                        version,
                    )
                except UnidentifiedImageError as e:
                    log(f"Unable to retrieve {img_name}\n{e}")
                except FileNotFoundError as e:
                    log(f"Non existing {img_name}\n{e}")

    # Check if there is a manifest work and a list of images url and process it
    elif manifest_first and f"{work_abbr}{work.id}.txt" in os.listdir(
        BASE_DIR / IMG_PATH
    ):
        with open(f"{BASE_DIR}/{IMG_PATH}/{work_abbr}{work.id}.txt", "r") as f:
            for counter, line in enumerate(f.read().splitlines(), start=1):
                img_dimensions = {
                    "height": line.split(" ")[0],
                    "width": line.split(" ")[1],
                }
                img_url = line.split(" ")[2]

                build_canvas_and_annotation(
                    seq, counter, img_url, img_dimensions, version
                )

    # # Check if there is a manifest work and process it
    # elif manifest_first:
    #     for counter, path in enumerate(
    #             sorted(glob(f"{BASE_DIR}/{IMG_PATH}/{work_abbr}{work.id}_*.jpg")),
    #             start=1,
    #     ):
    #         img_name = os.path.basename(path)
    #         try:
    #             image = Image.open(path)
    #             build_canvas_and_annotation(seq, counter, img_name, image, version)
    #         except UnidentifiedImageError as e:
    #             log(f"[process_images] Unable to retrieve {img_name}\n{e}")
    #             continue
    #         except FileNotFoundError as e:
    #             log(f"[process_images] Non existing {img_name}\n{e}")
    # If none of the above, raise an exception
    else:
        raise Exception("There is no manifest!")


def build_canvas_and_annotation(seq, counter, image_name, image, version):
    """
    Build the canvas and annotation for each image
    Called for each manifest (v2) image when a witness is being indexed
    """
    try:
        h, w = int(image["height"]), int(image["width"])
    except TypeError:
        h, w = image.height, image.width
    except ValueError:
        h, w = 900, 600
    # Build the canvas
    canvas = seq.canvas(ident=f"c{counter}", label=f"Page {counter}")
    canvas.set_hw(h, w)
    # Build the image annotation
    anno = canvas.annotation(ident=f"a{counter}")
    if re.match(r"https?://(.*?)/", image_name):
        img = anno.image(image_name, iiif=False)
        setattr(img, "format", "image/jpeg")
    else:
        img = anno.image(ident=image_name, iiif=True)
    img.set_hw(h, w)
    if version == "auto":
        anno_list = canvas.annotationList(ident=f"anno-{counter}")
        anno = anno_list.annotation(ident=f"a-list-{counter}")
        anno.text("Annotation")


def annotate_canvas(id, version, work, work_abbr, canvas, anno, num_anno):
    base_url = f"{VHS_APP_URL}/{APP_NAME}/iiif/{version}/{work}/{work_abbr}-{id}"

    anno2_2 = anno[2] // 2
    anno3_2 = anno[3] // 2

    data_paper = (
        '{"strokeWidth":1,"rotation":0,"deleteIcon":null,"rotationIcon":null,'
        '"group":null,"editable":true,"annotation":null}'
    )

    return {
        "@id": f"{SAS_APP_URL}/annotation/{work_abbr}-{id}-{canvas}-{num_anno + 1}",
        "@type": "oa:Annotation",
        "dcterms:created": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "dcterms:modified": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "resource": [
            {
                "@type": "dctypes:Text",
                f"{SAS_APP_URL}/full_text": "",
                "format": "text/html",
                "chars": "<p></p>",
            }
        ],
        "on": [
            {
                "@type": "oa:SpecificResource",
                "within": {
                    "@id": f"{base_url}/manifest.json",
                    "@type": "sc:Manifest",
                },
                "selector": {
                    "@type": "oa:Choice",
                    "default": {
                        "@type": "oa:FragmentSelector",
                        "value": f"xywh={anno[0]},{anno[1]},{anno[2]},{anno[3]}",
                    },
                    "item": {
                        "@type": "oa:SvgSelector",
                        "value": "<svg xmlns='http://www.w3.org/2000/svg'><path xmlns='http://www.w3.org/2000/svg' "
                        f"d='M{anno[0]} {anno[1]} h {anno2_2} v 0 h {anno2_2} v {anno3_2} v {anno3_2} "
                        f"h -{anno2_2} h -{anno2_2} v -{anno3_2}Z' data-paper-data='{data_paper}'"
                        f"id='rectangle_{work_abbr}{id}-{canvas}-{num_anno + 1}' fill-opacity='0' "
                        f"fill='#00ff00' fill-rule='nonzero' stroke='#00ff00' stroke-width='1' "
                        f"stroke-linecap='butt' stroke-linejoin='miter' stroke-miterlimit='10' "
                        f"stroke-dashoffset='0' style='mix-blend-mode: normal'/></svg",
                    },
                },
                "full": f"{base_url}/canvas/c{canvas}.json",
            }
        ],
        "motivation": ["oa:commenting", "oa:tagging"],
        "@context": "http://iiif.io/api/presentation/2/context.json",
    }


def manifest_witness(id, wit_abbr=MS_ABBR, version=MANIFEST_AUTO):
    """
    Build a manuscript manifest using iiif-prezi library
    IIIF Presentation API 2.0
    """
    wit_name = MS if wit_abbr == MS_ABBR else VOL
    witness = get_object_or_404(Manuscript if wit_abbr == MS_ABBR else Volume, pk=id)
    fac = ManifestFactory(
        mdbase=f"{VHS_APP_URL}/{APP_NAME}/iiif/{version}/{wit_name}/{wit_abbr}-{id}/",
        imgbase=f"{CANTALOUPE_APP_URL}/iiif/2/",
    )

    fac.set_iiif_image_info(version="2.0", lvl="2")
    # Build the manifest
    manifest = fac.manifest(ident="manifest", label=witness.__str__())
    manifest.set_metadata(witness.get_metadata())

    # Set the manifest's attribution, description, and viewing hint
    manifest.attribution = f"{APP_NAME_UPPER} platform"
    manifest.description = APP_DESCRIPTION
    manifest.viewingHint = "individuals"

    # And walk through the pages
    seq = manifest.sequence(ident="normal", label="Normal Order")
    process_images(witness, seq, version)

    return manifest
