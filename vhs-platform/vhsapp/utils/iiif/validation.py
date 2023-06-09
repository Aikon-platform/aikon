import re

from tripoli import IIIFValidator
from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from vhsapp.utils.functions import get_json, create_dir, save_img


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


# NOT USED
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


# NOT USED
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
