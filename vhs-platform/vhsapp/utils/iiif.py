import json
import re
import time
from urllib.parse import urlparse

import requests
from django.core.exceptions import ValidationError
from tripoli import IIIFValidator


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
