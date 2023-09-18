from glob import glob

from django.utils.safestring import mark_safe

from app.webapp.utils.constants import (
    MANIFEST_V1,
    MANIFEST_V2,
    APP_NAME_UPPER,
    APP_DESCRIPTION,
)
from app.webapp.utils.functions import get_icon, anno_btn, get_action
from app.webapp.models.utils.constants import VOL_ABBR, MS_ABBR, VOL, MS
from app.config.settings import (
    SAS_APP_URL,
    APP_URL,
    CANTALOUPE_APP_URL,
    APP_NAME,
    APP_LANG,
)
from app.webapp.utils.iiif import IIIF_ICON
from app.webapp.utils.iiif.manifest import gen_manifest_url


def get_link_manifest(wit_id, manifest_url, tag_id="url_manifest_"):
    return f"<a id='{tag_id}{wit_id}' href='{manifest_url}' target='_blank'>{manifest_url} {IIIF_ICON}</a>"


def gen_btn(wit_id, action="view", vers=MANIFEST_V1, wit_type=VOL.lower()):
    msg_id = f"message_auto_{wit_id}" if vers == MANIFEST_V1 else f"message_{wit_id}"

    if action == "no_manifest" or action == "no_anno":
        return mark_safe(anno_btn(wit_id, action))

    obj_ref = f"{APP_NAME}/iiif/{vers}/{wit_type}/{wit_id}"
    manifest = f"{APP_URL}/{obj_ref}/manifest.json"

    if vers == MANIFEST_V1:
        tag_id = "iiif_auto_"
        download_url = f"/{obj_ref}/annotation/"
        anno_type = "CSV"
    else:
        tag_id = f"url_manifest_"
        download_url = f"{SAS_APP_URL}/search-api/{wit_id}/search/"
        anno_type = "JSON"

    return mark_safe(
        f"{get_link_manifest(wit_id, manifest, tag_id)}<br>{anno_btn(wit_id, action)}"
        f'<a href="{download_url}" target="_blank">{get_icon("download")} {get_action("download")} annotations ({anno_type})</a>'
        f'<span id="{msg_id}" style="color:#FF0000"></span>'
    )


def gen_manifest_btn(wit_id, wit_type=MS, has_manifest=True):
    manifest = digit.gen_manifest_url()
    mf = (
        f"<a href='{manifest}' target='_blank'>{IIIF_ICON}</a>"
        if has_manifest
        else "<span class='faded'>No manifest</span>"
    )
    return mark_safe(f"<div class='iiif-icon'>{mf}</div>")
