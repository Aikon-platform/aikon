from PIL import Image, UnidentifiedImageError
from iiif_prezi.factory import ManifestFactory, StructuralError

from app.webapp.models.annotation import Annotation
from app.webapp.models.digitization import Digitization
from app.webapp.utils.constants import (
    APP_NAME_UPPER,
    APP_DESCRIPTION,
)
from app.webapp.utils.paths import IMG_PATH
from app.config.settings import CANTALOUPE_APP_URL

from app.webapp.utils.logger import console, log
from app.webapp.utils.iiif.annotation import set_canvas

# NOTE img name = "{wit_abbr}{wit_id}_{digit_abbr}{digit_id}_{canvas_nb}.jpg"


def get_meta(metadatum, meta_type="label"):
    from app.webapp.utils.functions import mono_val

    if meta_type not in metadatum:
        return None
    meta_label = metadatum[meta_type]
    if type(meta_label) == str:
        return meta_label
    if type(meta_label) == list:
        for lang_label in meta_label:
            if "@language" in lang_label and lang_label["@language"] == "en":
                return mono_val(lang_label["@value"])
            if "language" in lang_label and lang_label["language"] == "en":
                return mono_val(lang_label["value"])
    if type(meta_label) == dict:
        if len(meta_label.keys()) == 1:
            return mono_val(meta_label.values()[0])
        if "en" in meta_label:
            return mono_val(meta_label["en"])
    return None


def get_meta_value(metadatum, label: str):
    meta_label = get_meta(metadatum, "label")
    if meta_label not in [label, label.capitalize(), f"@{label}"]:
        return None
    return get_meta(metadatum, "value")


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
                    Image.open(f"{IMG_PATH}/{img}"),
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
    manifest.set_metadata(metadata)

    # Set the manifest's attribution, description, and viewing hint
    manifest.attribution = f"{APP_NAME_UPPER} platform"
    manifest.description = APP_DESCRIPTION
    manifest.license = metadata.license
    # manifest.viewingHint = "individuals"

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
