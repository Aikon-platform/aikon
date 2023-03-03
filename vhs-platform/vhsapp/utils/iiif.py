import json
import re
import time
from urllib.parse import urlparse

import requests
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from tripoli import IIIFValidator
from vhsapp.utils.constants import APP_NAME, MANIFEST_AUTO, MANIFEST_V2
from vhsapp.models.constants import VOL_ABBR, MS_ABBR, VOL, MS
from vhsapp.utils.functions import get_icon, anno_btn

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


def validate_iiif_manifest(url):
    """
    Validate a IIIF manifest using Tripoli
    Check if the manifest conforms to the IIIF Presentation API 2.1 specification
    """
    try:
        response = requests.get(url)
        manifest = json.loads(response.text)
        validator = IIIFValidator()
        validator.validate(manifest)
    except Exception:
        raise ValidationError("IIIF manifest is not valid.")


def validate_manifest(manifest):
    validate_iiif_manifest(manifest)

    hostname, path = parse_manifest(manifest)
    if hostname != "gallica.bnf.fr":
        raise ValidationError("This format of manifest not supported for the moment.")
    validate_gallica_manifest(manifest, False)


def extract_images_from_iiif_manifest(url, image_path, work):
    """
    Extract all images from an IIIF manifest
    """
    response = requests.get(url)
    manifest = json.loads(response.text)
    image_counter = 1
    for sequence in manifest["sequences"]:
        for canvas in sequence["canvases"]:
            for image in canvas["images"]:
                image_url = (
                    f"{image['resource']['service']['@id']}/full/full/0/default.jpg"
                )
                image_response = requests.get(image_url)
                with open(f"{image_path}{work}_{image_counter:04d}.jpg", "wb") as f:
                    f.write(image_response.content)
                image_counter += 1
                time.sleep(15)


def gen_img_url(
    img,
    scheme="http",
    host="localhost",
    port=None,
    vers=2,
    res="full/full/0",
    color="default",
    ext="jpg",
):
    # E.g. "http://localhost/iiif/2/image_name.jpg/full/full/0/default.jpg"
    return f"{scheme}://{host}{f':{port}' if port else ''}/iiif/{vers}/{img}/{res}/{color}.{ext}"


def get_link_manifest(obj_id, manifest_url, tag_id="url_manifest_"):
    return f"<a id='{tag_id}{obj_id}' href='{manifest_url}' target='_blank'>{manifest_url} {IIIF_ICON}</a>"


def gen_btn(obj_id, action="VISUALIZE", vers=MANIFEST_AUTO, ps_type=VOL.lower()):
    obj_ref = f"{APP_NAME}/iiif/{vers}/{ps_type}/{obj_id}"
    manifest = f"http://localhost:8000/{obj_ref}/manifest.json"

    if vers == MANIFEST_AUTO:
        tag_id = f"iiif_auto_"
        message_id = f"message_auto_{obj_id}"
        download_url = f"/{obj_ref}/annotation/"
        anno_type = "CSV"
    else:
        tag_id = f"url_manifest_"
        message_id = f"message_{obj_id}"
        download_url = f"http://localhost:8888/search-api/{obj_id}/search/"
        anno_type = "JSON"

    return mark_safe(
        f"{get_link_manifest(obj_id, manifest, tag_id)}<br>{anno_btn(obj_id, action)}"
        f'<a href="{download_url}" target="_blank">{get_icon("download")} Download annotation ({anno_type})</a>'
        f'<span id="{message_id}" style="color:#FF0000"></span>'
    )


def gen_manifest_url(
    m_id,
    scheme="http",
    host="localhost",
    port=None,
    vers=MANIFEST_AUTO,
    m_type=VOL.lower(),
):
    return f"{scheme}://{host}{f':{port}' if port else ''}/{APP_NAME}/iiif/{vers}/{m_type}/{m_id}/manifest.json"
