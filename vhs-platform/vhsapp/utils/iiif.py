import fnmatch
import os
import re

import requests
import time
from glob import glob
from datetime import datetime
from PIL import Image, UnidentifiedImageError
from django.shortcuts import get_object_or_404
from iiif_prezi.factory import ManifestFactory
from pikepdf import Pdf
from tripoli import IIIFValidator
from pathlib import Path
import shutil
from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe

from vhsapp.utils.constants import (
    APP_NAME,
    MANIFEST_AUTO,
    MANIFEST_V2,
    APP_NAME_UPPER,
    APP_DESCRIPTION,
)
from vhsapp.utils.functions import get_json, create_dir, save_img
from vhsapp.utils.paths import MEDIA_PATH, IMG_PATH, BASE_DIR
from vhsapp.utils.functions import get_icon, anno_btn
from vhsapp.models.constants import VOL_ABBR, MS_ABBR, VOL, MS
from vhs.settings import SAS_APP_URL, VHS_APP_URL, CANTALOUPE_APP_URL
from vhsapp.models.witness import Volume, Manuscript
from vhsapp.utils.logger import iiif_log, console, log


IIIF_ICON = "<img alt='IIIF' src='https://iiif.io/assets/images/logos/logo-sm.png' height='15'/>"


def parse_manifest(manifest):
    url = urlparse(manifest)
    return url.hostname, url.path.strip("/").split("/")


def validate_gallica_manifest(manifest, check_hostname=True):
    """
    Validate the pattern of a Gallica manifest URL
    """
    if (
        check_hostname
        and re.match(r"https?://(.*?)/", manifest).group(1) != "gallica.bnf.fr"
    ):
        # Check if the hostname of the URL matches the desired pattern
        raise ValidationError("Not a Gallica manifest")

    # Define the regular expression pattern for a valid Gallica manifest URL
    pattern = re.compile(
        r"https://gallica.bnf.fr/iiif/ark:/12148/[a-z0-9]+/manifest.json"
    )
    # Check if the URL matches the pattern
    if not bool(pattern.match(manifest)):
        raise ValidationError("Gallica manifest URL is not valid.")


def validate_gallica_manifest_url(value):
    """
    Validate the pattern of a Gallica manifest URL
    """
    # hostname = re.match(r"https?://(.*?)/", value).group(1)
    # # Check if the hostname of the URL matches the desired pattern
    # if hostname == "gallica.bnf.fr":

    # Define the regular expression pattern for a valid Gallica manifest URL
    pattern = re.compile(
        r"https://gallica.bnf.fr/iiif/ark:/12148/[a-z0-9]+/manifest.json"
    )
    match = bool(pattern.match(value))
    # Check if the URL matches the pattern
    if not match:
        raise ValidationError("Invalid Gallica manifest")


def validate_iiif_manifest(url):
    """
    Validate a IIIF manifest using Tripoli
    Check if the manifest conforms to the IIIF Presentation API 2.1 specification
    """
    try:
        manifest = get_json(url)
        validator = IIIFValidator()
        validator.validate(manifest)

    except Exception:
        raise ValidationError("The URL is not a valid IIIF manifest")


def validate_manifest(manifest):
    # validate_iiif_manifest(manifest)
    hostname, path = parse_manifest(manifest)
    if hostname == "gallica.bnf.fr":
        validate_gallica_manifest(manifest, False)


def get_id(dic):
    if type(dic) == list:
        dic = dic[0]

    if type(dic) == dict:
        try:
            return dic["@id"]
        except KeyError:
            try:
                return dic["id"]
            except KeyError as e:
                log(f"[Get id] No id provided {e}")

    if type(dic) == str:
        return dic

    return None


def get_img_rsrc(iiif_img):
    try:
        img_rscr = iiif_img["resource"]
    except KeyError:
        try:
            img_rscr = iiif_img["body"]
        except KeyError:
            return None
    return img_rscr


def get_canvas_img(canvas_img, only_img_url=False):
    img_url = get_id(canvas_img["resource"]["service"])
    if only_img_url:
        return img_url
    return get_img_id(canvas_img["resource"]), img_url


def get_item_img(item_img, only_img_url=False):
    img_url = get_id(item_img["body"]["service"][0])
    if only_img_url:
        return img_url
    return get_img_id(item_img), img_url


def get_img_id(img):
    img_id = get_id(img)
    if ".jpg" in img_id:
        try:
            return img_id.split("/")[-5]
        except IndexError:
            return None
        # return Path(urlparse(img_id).path).parts[-5]
    return img_id.split("/")[-1]


def get_formatted_size(width="", height=""):
    if not width and not height:
        return "full"
    return f"{width or ''},{height or ''}"


def get_iiif_resources(manifest, only_img_url=False):
    try:
        img_list = [canvas["images"] for canvas in manifest["sequences"][0]["canvases"]]
        # img_info = [get_canvas_img(img, only_img_url) for imgs in img_list for img in imgs]
        img_info = [get_img_rsrc(img) for imgs in img_list for img in imgs]
    except KeyError:
        try:
            img_list = [
                item
                for items in manifest["items"]
                for item in items["items"][0]["items"]
            ]
            # img_info = [get_item_img(img, only_img_url) for img in img_list]
            img_info = [get_img_rsrc(img) for img in img_list]
        except KeyError as e:
            log(
                f"[get_iiif_resources] Unable to retrieve resources from manifest {manifest}\n{e}"
            )
            return []

    return img_info


def extract_images_from_iiif_manifest(manifest_url, work):
    """
    Extract all images from an IIIF manifest
    """
    manifest = get_json(manifest_url)
    if manifest is not None:
        # manifest_id = Path(urlparse(get_id(manifest)).path).parent.name
        i = 1
        for img_rscr in get_iiif_resources(manifest, True):
            is_downloaded = save_iiif_img(img_rscr, i, work)
            i += 1
            if is_downloaded:
                time.sleep(5 if "gallica" in manifest_url else 0.25)


def get_reduced_size(size, min_size=1500):
    size = int(size)
    if size < min_size:
        return ""
    if size > min_size * 2:
        return str(int(size / 2))
    return str(min_size)


def save_iiif_img(img_rscr, i, work, size="full", re_download=False):
    img_name = f"{work}_{i:04d}.jpg"

    if os.path.isfile(BASE_DIR / IMG_PATH / img_name) and not re_download:
        # if the img is already downloaded, don't download it again
        return False

    img_url = get_id(img_rscr["service"])
    iiif_url = f"{img_url}/full/{size}/0/default.jpg"

    with requests.get(iiif_url, stream=True) as response:
        response.raw.decode_content = True
        try:
            img = Image.open(response.raw)
        except UnidentifiedImageError:
            if size == "full":
                size = get_reduced_size(img_rscr["width"])
                save_iiif_img(img_rscr, i, work, get_formatted_size(size))
                return
            else:
                log(f"[save_iiif_img] Failed to extract images from {img_url}")
                iiif_log(img_url)
                return

        save_img(img, img_name, f"Failed to extract from {img_url}")
    return True


def gen_iiif_url(
    img,
    scheme="http",
    host="localhost",
    port=8182,
    vers=2,
    res="full/full/0",
    color="default",
    ext="jpg",
):
    # E.g. "http://localhost/iiif/2/image_name.jpg/full/full/0/default.jpg"
    # return f"{scheme}://{host}{f':{port}' if port else ''}/iiif/{vers}/{img}/{res}/{color}.{ext}"
    return f"{CANTALOUPE_APP_URL}/iiif/{vers}/{img}/{res}/{color}.{ext}"


def get_link_manifest(obj_id, manifest_url, tag_id="url_manifest_"):
    return f"<a id='{tag_id}{obj_id}' href='{manifest_url}' target='_blank'>{manifest_url} {IIIF_ICON}</a>"


def gen_btn(obj_id, action="VISUALIZE", vers=MANIFEST_AUTO, ps_type=VOL.lower()):
    msg_id = f"message_auto_{obj_id}" if vers == MANIFEST_AUTO else f"message_{obj_id}"

    if action == "NO MANIFEST" or action == "NO ANNOTATION YET":
        return mark_safe(anno_btn(obj_id, action))

    ps_prefix = VOL_ABBR if ps_type == VOL.lower() else MS_ABBR
    obj_ref = f"{APP_NAME}/iiif/{vers}/{ps_type}/{ps_prefix}-{obj_id}"
    manifest = f"{VHS_APP_URL}/{obj_ref}/manifest.json"

    if vers == MANIFEST_AUTO:
        tag_id = f"iiif_auto_"
        download_url = f"/{obj_ref}/annotation/"
        anno_type = "CSV"
    else:
        tag_id = f"url_manifest_"
        download_url = f"{SAS_APP_URL}/search-api/{obj_id}/search/"
        anno_type = "JSON"

    return mark_safe(
        f"{get_link_manifest(obj_id, manifest, tag_id)}<br>{anno_btn(obj_id, action)}"
        f'<a href="{download_url}" target="_blank">{get_icon("download")} Download annotation ({anno_type})</a>'
        f'<span id="{msg_id}" style="color:#FF0000"></span>'
    )


def gen_manifest_url(
    m_id,
    scheme="http",
    host="localhost",
    port=8182,
    vers=MANIFEST_AUTO,
    m_type=VOL.lower(),
):
    # return f"{scheme}://{host}{f':{port}' if port else ''}/{APP_NAME}/iiif/{vers}/{m_type}/{m_id}/manifest.json"
    return f"{CANTALOUPE_APP_URL}/{APP_NAME}/iiif/{vers}/{m_type}/{m_id}/manifest.json"


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

    # Check if there is a manifest work and process it
    elif manifest_first:
        for counter, path in enumerate(
            sorted(glob(f"{BASE_DIR}/{IMG_PATH}/{work_abbr}{work.id}_*.jpg")),
            start=1,
        ):
            img_name = os.path.basename(path)
            try:
                image = Image.open(path)
                build_canvas_and_annotation(seq, counter, img_name, image, version)
            except UnidentifiedImageError as e:
                log(f"[process_images] Unable to retrieve {img_name}\n{e}")
                continue
            except FileNotFoundError as e:
                log(f"[process_images] Non existing {img_name}\n{e}")
    # If none of the above, raise an exception
    else:
        raise Exception("There is no manifest!")


def build_canvas_and_annotation(seq, counter, image_name, image, version):
    """
    Build the canvas and annotation for each image
    Called for each manifest (v2) image when a witness is being indexed
    """
    h, w = image.height, image.width
    # Build the canvas
    canvas = seq.canvas(ident=f"c{counter}", label=f"Page {counter}")
    canvas.set_hw(h, w)
    # Build the image annotation
    anno = canvas.annotation(ident=f"a{counter}")
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

    d = f"M{anno[0]} {anno[1]} h {anno2_2} v 0 h {anno2_2} v {anno3_2} v {anno3_2} h -{anno2_2} h -{anno2_2} v -{anno3_2}Z"
    r_id = f"rectangle_{work_abbr}{id}-{canvas}-{num_anno + 1}"

    svg_anno = f"""
        <svg xmlns='http://www.w3.org/2000/svg'>
          <path xmlns='http://www.w3.org/2000/svg'
                d='{d}'
                id='{r_id}'
                data-paper-data='{{"strokeWidth":1,"rotation":0,"deleteIcon":null,"rotationIcon":null,"group":null,"editable":true,"annotation":null}}'
                fill-opacity='0'
                fill='#00ff00'
                fill-rule='nonzero'
                stroke='#00ff00'
                stroke-width='1'
                stroke-linecap='butt'
                stroke-linejoin='miter'
                stroke-miterlimit='10'
                stroke-dashoffset='0'
                style='mix-blend-mode: normal'/>
        </svg>"""

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
                        "value": svg_anno,
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


def has_manifest(img_prefix):
    # if there is at least one image file named after the current witness
    if len(glob(f"{BASE_DIR}/{IMG_PATH}/{img_prefix}_*.jpg")) > 0:
        return True
    return False


def has_annotations(witness, wit_type):
    # if there is at least one image file named after the current witness
    wit_dir = "manuscripts" if wit_type == "ms" else "volumes"
    if len(glob(f"{BASE_DIR}/{MEDIA_PATH}/{wit_dir}/annotation/{witness.id}.txt")) > 0:
        return True
    return False
