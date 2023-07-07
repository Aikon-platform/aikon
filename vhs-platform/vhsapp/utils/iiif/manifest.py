import os
import re

from glob import glob

from PIL import Image, UnidentifiedImageError
from django.shortcuts import get_object_or_404
from iiif_prezi.factory import ManifestFactory, StructuralError
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
from vhsapp.utils.iiif.annotation import set_canvas


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
                set_canvas(seq, counter, img_name, Image.open(img.image), version)
            except UnidentifiedImageError as e:
                log(f"[process_images] Unable to retrieve {img_name}\n{e}")
            except FileNotFoundError as e:
                log(f"[process_images] Non existing {img_name}\n{e}")

    # Check if there is a PDF work and process it
    elif pdf_first:  # PDF
        # TODO: factorize with pdf_to_img() in functions.py
        with Pdf.open(f"{BASE_DIR}/{MEDIA_PATH}/{pdf_first.pdf}") as pdf_file:
            for counter in range(1, len(pdf_file.pages) + 1):
                img_name = pdf_first.pdf.name.split("/")[-1].replace(
                    ".pdf", f"_{counter:04d}.jpg"
                )
                try:
                    set_canvas(
                        seq,
                        counter,
                        img_name,
                        Image.open(f"{BASE_DIR}/{IMG_PATH}/{img_name}"),
                        version,
                    )
                except UnidentifiedImageError as e:
                    log(f"[process_images] Unable to retrieve {img_name}\n{e}")
                except FileNotFoundError as e:
                    log(f"[process_images] Non existing {img_name}\n{e}")

    # Check if there is a manifest work and a list of images url and process it
    # elif manifest_first and f"{work_abbr}{work.id}.txt" in os.listdir(
    #     BASE_DIR / IMG_PATH
    # ):
    #     with open(f"{BASE_DIR}/{IMG_PATH}/{work_abbr}{work.id}.txt", "r") as f:
    #         for counter, line in enumerate(f.read().splitlines(), start=1):
    #             img_dimensions = {
    #                 "height": line.split(" ")[0],
    #                 "width": line.split(" ")[1],
    #             }
    #             img_url = line.split(" ")[2]
    #
    #             set_canvas(
    #                 seq, counter, img_url, img_dimensions, version
    #             )

    # Check if there is a manifest work and process it
    elif manifest_first:
        for counter, path in enumerate(
            sorted(glob(f"{BASE_DIR}/{IMG_PATH}/{work_abbr}{work.id}_*.jpg")),
            start=1,
        ):
            img_name = os.path.basename(path)
            try:
                set_canvas(seq, counter, img_name, Image.open(path), version)
            except UnidentifiedImageError as e:
                log(f"[process_images] Unable to retrieve {img_name}\n{e}")
                continue
            except FileNotFoundError as e:
                log(f"[process_images] Non existing {img_name}\n{e}")
    # If none of the above, raise an exception
    else:
        raise Exception("There is no manifest!")


def manifest_witness(id, wit_abbr=MS_ABBR, version=MANIFEST_AUTO):
    """
    Build a manuscript manifest using iiif-prezi library
    IIIF Presentation API 2.0
    """
    wit_name = MS if wit_abbr == MS_ABBR else VOL
    witness = get_object_or_404(Manuscript if wit_abbr == MS_ABBR else Volume, pk=id)
    fac = ManifestFactory(
        mdbase=f"{VHS_APP_URL}/{APP_NAME}/iiif/{version}/{wit_name}/{id}/",
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


def manifest_wit_type(wit_id, wit_type, version):
    try:
        manifest = manifest_witness(
            wit_id, VOL_ABBR if wit_type == VOL else MS_ABBR, version
        )
    except Exception as e:
        error = f"Unable to create manifest for {wit_type} n°{wit_id} (probably no {wit_type}): {e}"
        log(f"[manifest_wit_type] {error}")
        return {
            "error": "Unable to create a valid manifest",
            "reason": error,
        }

    try:
        return manifest.toJSON(top=True)
    except StructuralError as e:
        error = f"Unable to create manifest for {wit_type} n°{wit_id} (probably no images):\n{e}"
        log(f"[manifest_wit_type] {error}")
        return {
            "error": "Unable to create a valid manifest",
            "reason": error,
        }


def has_manifest(work):
    # if there is at least one image file named after the current witness
    if (
        len(glob(f"{BASE_DIR}/{IMG_PATH}/{work}_*.jpg"))
        or len(glob(f"{BASE_DIR}/{IMG_PATH}/{work}.txt")) > 0
    ):
        return True
    return False


def gen_manifest_url(wit_id, vers=MANIFEST_AUTO, wit_type=VOL.lower()):
    wit_abbr = VOL_ABBR if wit_type == VOL.lower() else MS_ABBR
    return (
        f"{CANTALOUPE_APP_URL}/{APP_NAME}/iiif/{vers}/{wit_type}/{wit_id}/manifest.json"
    )