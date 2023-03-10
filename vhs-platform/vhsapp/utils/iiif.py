import os
import re
import json
import requests
import time
from glob import glob
from datetime import datetime
from PIL import Image
from pikepdf import Pdf
from tripoli import IIIFValidator
from django.core.exceptions import ValidationError
from vhs.settings import SAS_APP_URL, VHS_APP_URL
from vhsapp.utils.constants import MS_ABBR, VOL_ABBR
from vhsapp.utils.functions import log
from vhsapp.utils.paths import MEDIA_PATH, IMG_PATH


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
    try:
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
    except Exception as e:
        # Log an error message
        log(f"Failed to extract images from {url}: {e}")


def process_images(work, seq, version):
    """
    Process the images of a work and add them to a sequence
    """
    if hasattr(work, "imagemanuscript_set"):
        images = work.imagemanuscript_set.all()
        pdf_first = work.pdfmanuscript_set.first()
        manifest_first = work.manifestmanuscript_set.first()
        work_abbr = MS_ABBR
    else:
        images = work.imagevolume_set.all()
        pdf_first = work.pdfvolume_set.first()
        manifest_first = work.manifestvolume_set.first()
        work_abbr = VOL_ABBR
    # Check if there are any work images and process them
    if images:
        for counter, img in enumerate(images, start=1):
            image_name = img.image.url.split("/")[-1]
            image = Image.open(img.image)
            build_canvas_and_annotation(seq, counter, image_name, image, version)
    # Check if there is a PDF work and process it
    elif pdf_first:
        with Pdf.open(f"{MEDIA_PATH}{pdf_first.pdf}") as pdf_file:
            total_pages = len(pdf_file.pages)
            for counter in range(1, total_pages + 1):
                image_name = pdf_first.pdf.name.split("/")[-1].replace(
                    ".pdf", f"_{counter:04d}.jpg"
                )
                image = Image.open(f"{MEDIA_PATH}{IMG_PATH}{image_name}")
                build_canvas_and_annotation(seq, counter, image_name, image, version)
    # Check if there is a manifest work and process it
    elif manifest_first:
        for counter, path in enumerate(
            sorted(glob(f"{MEDIA_PATH}{IMG_PATH}{work_abbr}{work.id}_*.jpg")),
            start=1,
        ):
            image_name = os.path.basename(path)
            image = Image.open(path)
            build_canvas_and_annotation(seq, counter, image_name, image, version)
    # If none of the above, raise an exception
    else:
        raise Exception("There is no manifest!")


def build_canvas_and_annotation(seq, counter, image_name, image, version):
    """
    Build the canvas and annotation for each image
    """
    # Build the canvas
    cvs = seq.canvas(ident=f"c{counter}", label=f"Page {counter}")
    cvs.set_hw(image.height, image.width)
    # Build the image annotation
    anno = cvs.annotation(ident=f"a{counter}")
    img = anno.image(ident=image_name, iiif=True)
    img.set_hw(image.height, image.width)
    if version == "auto":
        anno_list = cvs.annotationList(ident=f"anno-{counter}")
        anno = anno_list.annotation(ident=f"a-list-{counter}")
        anno.text("Annotation")


def annotate_canvas(id, version, work, work_abbr, canvas, anno, num_anno):
    anno_json = {
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
                    "@id": f"{VHS_APP_URL}/vhs/iiif/{version}/{work}/{work_abbr}-{id}/manifest.json",
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
                "full": f"{VHS_APP_URL}/vhs/iiif/{version}/{work}/{work_abbr}-{id}/canvas/c{canvas}.json",
            }
        ],
        "motivation": ["oa:commenting", "oa:tagging"],
        "@context": "http://iiif.io/api/presentation/2/context.json",
    }
    return anno_json
