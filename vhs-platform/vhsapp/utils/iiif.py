import re
import json
import requests
import time
from datetime import datetime
from tripoli import IIIFValidator
from django.core.exceptions import ValidationError
from vhs.settings import SAS_APP_URL, VHS_APP_URL


def validate_gallica_manifest_url(value):
    """
    Validate the pattern of a Gallica manifest URL
    """
    hostname = re.match(r"https?://(.*?)/", value).group(1)
    # Check if the hostname of the URL matches the desired pattern
    if hostname == "gallica.bnf.fr":
        # Define the regular expression pattern for a valid Gallica manifest URL
        pattern = re.compile(
            r"https://gallica.bnf.fr/iiif/ark:/12148/[a-z0-9]+/manifest.json"
        )
        match = bool(pattern.match(value))
        # Check if the URL matches the pattern
        if not match:
            raise ValidationError("URL de manifeste Gallica non valide.")


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
        raise ValidationError("Manifeste IIIF non valide.")


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


def annotate_canvas(id, version, work, work_abbr, canvas, anno, num_anno):
    anno_json = {
        "@id": f"{SAS_APP_URL}annotation/{work_abbr}-{id}-{canvas}-{num_anno + 1}",
        "@type": "oa:Annotation",
        "dcterms:created": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "dcterms:modified": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "resource": [
            {
                "@type": "dctypes:Text",
                f"{SAS_APP_URL}full_text": "",
                "format": "text/html",
                "chars": "<p></p>",
            }
        ],
        "on": [
            {
                "@type": "oa:SpecificResource",
                "within": {
                    "@id": f"{VHS_APP_URL}vhs/iiif/{version}/{work}/{work_abbr}-{id}/manifest.json",
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
                        "value": "<svg xmlns='http://www.w3.org/2000/svg'><path xmlns='http://www.w3.org/2000/svg' d='M"
                        + str(anno[0])
                        + " "
                        + str(anno[1])
                        + " h "
                        + str(anno[2] // 2)
                        + " v 0 h "
                        + str(anno[2] // 2)
                        + " v "
                        + str(anno[3] // 2)
                        + " v "
                        + str(anno[3] // 2)
                        + " h -"
                        + str(anno[2] // 2)
                        + " h -"
                        + str(anno[2] // 2)
                        + " v -"
                        + str(anno[3] // 2)
                        + 'Z\' data-paper-data=\'{"strokeWidth":1,"rotation":0,"deleteIcon":null,"rotationIcon":null,"group":null,"editable":true,"annotation":null}\' id=\'rectangle_'
                        + work_abbr
                        + str(id)
                        + "-"
                        + str(canvas)
                        + "-"
                        + str(num_anno + 1)
                        + "' fill-opacity='0' fill='#00ff00' fill-rule='nonzero' stroke='#00ff00' stroke-width='1' stroke-linecap='butt' stroke-linejoin='miter' stroke-miterlimit='10' stroke-dashoffset='0' style='mix-blend-mode: normal'/></svg>",
                    },
                },
                "full": f"{VHS_APP_URL}vhs/iiif/{version}/{work}/{work_abbr}-{id}/canvas/c{canvas}.json",
            }
        ],
        "motivation": ["oa:commenting", "oa:tagging"],
        "@context": "http://iiif.io/api/presentation/2/context.json",
    }
    return anno_json
