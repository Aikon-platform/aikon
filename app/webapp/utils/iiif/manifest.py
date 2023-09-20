import os

from glob import glob
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from django.shortcuts import get_object_or_404
from iiif_prezi.factory import ManifestFactory, StructuralError

from app.webapp.models import get_wit_abbr
from app.webapp.models.annotation import Annotation
from app.webapp.models.digitization import Digitization
from app.webapp.utils.constants import (
    MANIFEST_V1,
    MANIFEST_V2,
    APP_NAME_UPPER,
    APP_DESCRIPTION,
)
from app.webapp.utils.functions import get_imgs
from app.webapp.utils.paths import MEDIA_DIR, IMG_PATH, BASE_DIR
from app.webapp.models.utils.constants import VOL_ABBR, MS_ABBR, VOL, MS
from app.config.settings import SAS_APP_URL, APP_URL, CANTALOUPE_APP_URL, APP_NAME
from app.webapp.models.volume import Volume
from app.webapp.models.witness import Witness

# from app.webapp.models.witness import Volume, Manuscript
from app.webapp.utils.logger import iiif_log, console, log
from app.webapp.utils.iiif.annotation import set_canvas

# NOTE img name = "{wit_abbr}{wit_id}_{digit_abbr}{digit_id}_{canvas_nb}.jpg"


def process_images(obj: Digitization | Annotation, seq, version=None):
    """
    Process the images of a witness and add them to a sequence
    """
    class_name = obj.__class__.__name__

    try:
        for counter, img in enumerate(obj.get_imgs(), start=1):
            try:
                set_canvas(
                    seq,
                    counter,
                    img,
                    Image.open(f"{BASE_DIR}/{IMG_PATH}/{img}"),
                    version,
                )
            except UnidentifiedImageError as e:
                log(f"[process_images] Unable to retrieve {img}", e)
            except FileNotFoundError as e:
                log(f"[process_images] Non existing {img}", e)
    except Exception as e:
        log(f"[process_images] Couldn't retrieve image for {class_name} n°{obj.id}", e)
        return False
    return True


def gen_manifest_json(obj: Digitization | Annotation, version=None):
    """
    Build a manuscript manifest using iiif-prezi library
    IIIF Presentation API 2.0
    """
    class_name = obj.__class__.__name__

    try:
        fac = ManifestFactory(
            mdbase=obj.gen_manifest_url(only_base=True, version=version),
            imgbase=f"{CANTALOUPE_APP_URL}/iiif/2/",
        )
    except Exception as e:
        log(
            f"[gen_manifest_json] Unable to create manifest for {class_name} n°{obj.id}",
            e,
        )
        return False

    fac.set_iiif_image_info(version="2.0", lvl="2")
    # Build the manifest
    manifest = fac.manifest(ident="manifest", label=obj.__str__())
    metadata = obj.get_metadata()
    # metadata["Is annotated"] = obj.has_annotations()
    manifest.set_metadata(metadata)

    # Set the manifest's attribution, description, and viewing hint
    manifest.attribution = f"{APP_NAME_UPPER} platform"
    manifest.description = APP_DESCRIPTION
    manifest.viewingHint = "individuals"

    try:
        # And walk through the pages
        seq = manifest.sequence(ident="normal", label="Normal Order")
        process_images(obj, seq, version)
    except Exception as e:
        log(
            f"[gen_manifest_json] Unable to process images for {class_name} n°{obj.id}",
            e,
        )
        return False

    return manifest
