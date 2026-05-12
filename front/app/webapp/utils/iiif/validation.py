import re

from tripoli import IIIFValidator
from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from app.webapp.utils.functions import get_json


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


def validate_manifest(manifest):
    # validate_iiif_manifest(manifest)
    hostname, path = parse_manifest(manifest)
    if hostname == "gallica.bnf.fr":
        validate_gallica_manifest(manifest, False)
