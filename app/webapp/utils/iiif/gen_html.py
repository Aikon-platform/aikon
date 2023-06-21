from glob import glob

from django.utils.safestring import mark_safe

from app.webapp.utils.constants import (
    MANIFEST_AUTO,
    MANIFEST_V2,
    APP_NAME_UPPER,
    APP_DESCRIPTION,
)
from app.webapp.utils.functions import get_icon, anno_btn
from app.webapp.models.utils.constants import VOL_ABBR, MS_ABBR, VOL, MS
from app.config.settings import SAS_APP_URL, APP_URL, CANTALOUPE_APP_URL, APP_NAME
from app.webapp.utils.iiif import IIIF_ICON
from app.webapp.utils.iiif.manifest import gen_manifest_url


def get_link_manifest(obj_id, manifest_url, tag_id="url_manifest_"):
    return f"<a id='{tag_id}{obj_id}' href='{manifest_url}' target='_blank'>{manifest_url} {IIIF_ICON}</a>"


def gen_btn(obj_id, action="VISUALIZE", vers=MANIFEST_AUTO, wit_type=VOL.lower()):
    msg_id = f"message_auto_{obj_id}" if vers == MANIFEST_AUTO else f"message_{obj_id}"

    if action == "NO MANIFEST" or action == "NO ANNOTATION YET":
        return mark_safe(anno_btn(obj_id, action))

    obj_ref = f"{APP_NAME}/iiif/{vers}/{wit_type}/{obj_id}"
    manifest = f"{APP_URL}/{obj_ref}/manifest.json"

    if vers == MANIFEST_AUTO:
        tag_id = "iiif_auto_"
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


def gen_manifest_btn(obj_id, wit_type=MS, has_manifest=True):
    manifest = gen_manifest_url(obj_id, MANIFEST_AUTO, wit_type.lower())
    mf = (
        f"<a href='{manifest}' target='_blank'>{IIIF_ICON}</a>"
        if has_manifest
        else "<span class='faded'>No manifest</span>"
    )
    return mark_safe(f"<div class='iiif-icon'>{mf}</div>")
