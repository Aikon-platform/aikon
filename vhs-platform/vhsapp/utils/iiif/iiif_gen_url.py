from glob import glob

from django.utils.safestring import mark_safe

from vhsapp.utils.constants import (
    APP_NAME,
    MANIFEST_AUTO,
    MANIFEST_V2,
    APP_NAME_UPPER,
    APP_DESCRIPTION,
)
from vhsapp.utils.paths import MEDIA_PATH, IMG_PATH, BASE_DIR
from vhsapp.utils.functions import get_icon, anno_btn
from vhsapp.models.constants import VOL_ABBR, MS_ABBR, VOL, MS
from vhs.settings import SAS_APP_URL, VHS_APP_URL, CANTALOUPE_APP_URL


def get_link_manifest(obj_id, manifest_url, tag_id="url_manifest_"):
    return f"<a id='{tag_id}{obj_id}' href='{manifest_url}' target='_blank'>{manifest_url} {IIIF_ICON}</a>"


def gen_btn(obj_id, action="VISUALIZE", vers=MANIFEST_AUTO, ps_type=VOL.lower()):
    msg_id = f"message_auto_{obj_id}" if vers == MANIFEST_AUTO else f"message_{obj_id}"

    if action == "NO MANIFEST" or action == "NO ANNOTATION YET":
        return mark_safe(anno_btn(obj_id, action))

    ps_prefix = VOL_ABBR if ps_type == VOL.lower() else MS_ABBR
    obj_ref = f"{APP_NAME}/iiif/{vers}/{ps_type}/{ps_prefix}-{obj_id}"
    manifest = f"{VHS_APP_URL}/{obj_ref}/manifest.json"

    if vers == MANIFEST_AUTO:
        tag_id = f"iiif_auto_"
        download_url = f"/{obj_ref}/annotation/"
        anno_type = "CSV"
    else:
        tag_id = f"url_manifest_"
        download_url = f"{SAS_APP_URL}/search-api/{obj_id}/search/"
        anno_type = "JSON"

    return mark_safe(
        f"{get_link_manifest(obj_id, manifest, tag_id)}<br>{anno_btn(obj_id, action)}"
        f'<a href="{download_url}" target="_blank">{get_icon("download")} Download annotation ({anno_type})</a>'
        f'<span id="{msg_id}" style="color:#FF0000"></span>'
    )


def gen_manifest_url(
    m_id,
    scheme="http",
    host="localhost",
    port=8182,
    vers=MANIFEST_AUTO,
    m_type=VOL.lower(),
):
    # return f"{scheme}://{host}{f':{port}' if port else ''}/{APP_NAME}/iiif/{vers}/{m_type}/{m_id}/manifest.json"
    return f"{CANTALOUPE_APP_URL}/{APP_NAME}/iiif/{vers}/{m_type}/{m_id}/manifest.json"


def gen_iiif_url(
    img,
    scheme="http",
    host="localhost",
    port=8182,
    vers=2,
    res="full/full/0",
    color="default",
    ext="jpg",
):
    # E.g. "http://localhost/iiif/2/image_name.jpg/full/full/0/default.jpg"
    # return f"{scheme}://{host}{f':{port}' if port else ''}/iiif/{vers}/{img}/{res}/{color}.{ext}"
    return f"{CANTALOUPE_APP_URL}/iiif/{vers}/{img}/{res}/{color}.{ext}"


def has_manifest(work):
    # if there is at least one image file named after the current witness
    if (
        len(glob(f"{BASE_DIR}/{IMG_PATH}/{work}_*.jpg"))
        or len(glob(f"{BASE_DIR}/{IMG_PATH}/{work}.txt")) > 0
    ):
        return True
    return False


def has_annotations(witness, wit_type):
    # if there is at least one image file named after the current witness
    wit_dir = "manuscripts" if wit_type == "ms" else "volumes"
    if len(glob(f"{BASE_DIR}/{MEDIA_PATH}/{wit_dir}/annotation/{witness.id}.txt")) > 0:
        return True
    return False
