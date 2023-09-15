import os

from glob import glob
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from django.shortcuts import get_object_or_404
from iiif_prezi.factory import ManifestFactory, StructuralError

from app.webapp.models import get_wit_abbr
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
from app.webapp.utils.iiif.annotation import set_canvas, has_annotations


# TODO change MS/VOL
# NOTE img name = "{wit_abbr}{wit_id}_{digit_abbr}{digit_id}_{canvas_nb}.jpg"


def process_images(witness, seq, version):
    """
    Process the images of a witness and add them to a sequence
    """
    wit_ref = f"{witness.get_type()}{witness.id}"

    try:
        for counter, img in enumerate(get_imgs(wit_ref), start=1):
            try:
                set_canvas(
                    seq,
                    counter,
                    img,
                    Image.open(f"{BASE_DIR}/{IMG_PATH}/{img}"),
                    version,
                )
            except UnidentifiedImageError as e:
                log(f"[process_images] Unable to retrieve {img}\n{e}")
            except FileNotFoundError as e:
                log(f"[process_images] Non existing {img}\n{e}")
    except Exception as e:
        log(f"[process_images] Couldn't retrieve image for #{wit_ref}: {e}")
        return False
    return True


def manifest_witness(digit: Digitization, version=MANIFEST_V1):
    # TODO here digit
    """
    Build a manuscript manifest using iiif-prezi library
    IIIF Presentation API 2.0
    """
    wit_type = MS if wit_abbr == MS_ABBR else VOL
    try:
        witness = get_object_or_404(Witness, pk=wit_id)
    except Exception as e:
        log(f"[manifest_witness] Unable to retrieve {wit_type} n°{wit_id}: {e}")
        return False

    try:
        fac = ManifestFactory(
            mdbase=gen_manifest_base(digit, version),
            imgbase=f"{CANTALOUPE_APP_URL}/iiif/2/",
        )
    except Exception as e:
        log(
            f"[manifest_witness] Unable to create manifest for {wit_type} n°{wit_id}: {e}"
        )
        return False

    fac.set_iiif_image_info(version="2.0", lvl="2")
    # Build the manifest
    manifest = fac.manifest(ident="manifest", label=witness.__str__())
    metadata = digit.get_metadata()
    metadata["Is annotated"] = has_annotations(witness, wit_abbr)
    manifest.set_metadata(metadata)

    # Set the manifest's attribution, description, and viewing hint
    manifest.attribution = f"{APP_NAME_UPPER} platform"
    manifest.description = APP_DESCRIPTION
    manifest.viewingHint = "individuals"

    try:
        # And walk through the pages
        seq = manifest.sequence(ident="normal", label="Normal Order")
        process_images(witness, seq, version)
    except Exception as e:
        log(
            f"[manifest_witness] Unable to process images for {wit_type} n°{wit_id}: {e}"
        )
        return False

    return manifest


def manifest_wit_type(wit_id, wit_type, version):
    manifest = manifest_witness(digit, version)
    if not manifest:
        return {"error": "Unable to create a valid manifest"}

    try:
        return manifest.toJSON(top=True)
    except StructuralError as e:
        error = f"Unable to create manifest for {wit_type} n°{wit_id} (probably no images):\n{e}"
        log(f"[manifest_wit_type] {error}")
        return {
            "error": "Unable to create a valid manifest",
            "reason": error,
        }


def has_manifest(wit_ref):
    # if there is at least one image file named after the current witness
    if len(glob(f"{BASE_DIR}/{IMG_PATH}/{wit_ref}_*.jpg")):
        return True
    return False


def gen_manifest_base(digit: Digitization, vers=MANIFEST_V1):
    return f"{APP_URL}/{APP_NAME}/iiif/{vers}/{digit.get_wit_type()}/{digit.get_wit_id()}/{digit.id}"


def gen_manifest_url(digit: Digitization, vers=MANIFEST_V1):
    return f"{gen_manifest_base(digit, vers)}/manifest.json"
