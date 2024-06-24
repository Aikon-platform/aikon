from django.utils.safestring import mark_safe

from app.webapp.models.regions import Regions
from app.webapp.models.digitization import Digitization
from app.webapp.utils.constants import MANIFEST_V1, MANIFEST_V2
from app.webapp.utils.functions import get_icon, get_action, cls
from app.config.settings import (
    SAS_APP_URL,
    APP_URL,
    APP_NAME,
)
from app.webapp.utils.iiif import IIIF_ICON


def regions_btn(obj, action="view"):
    """
    obj: Regions | Digitization
    """
    disabled = ""
    btn = f"{get_action(action, 'upper')}"

    if action == "view":
        color = "#EFB80B"
        icon = get_icon("eye")
        # The link redirects to Mirador with no regions (Digitization) or automatic regions (Regions)
        link = f"{SAS_APP_URL}/indexView.html?iiif-content={obj.gen_manifest_url(version=MANIFEST_V1)}"
    elif action == "auto-view":
        color = "#EFB80B"
        icon = get_icon("eye")
        # The link redirects to Mirador with no regions (Digitization) or automatic regions (Regions)
        link = f"{SAS_APP_URL}/indexView.html?iiif-content={obj.gen_manifest_url(version=MANIFEST_V1)}"
    elif action == "edit":
        color = "#008CBA"
        icon = get_icon("pen-to-square")
        # The link redirects to the edit regions page (show_regions() view)
        link = f"{APP_URL}/{APP_NAME}/{obj.get_ref()}/show/"
    elif action == "final":
        color = "#4CAF50"
        icon = get_icon("check")
        # The link redirects to Mirador with corrected regions (Regions)
        link = f"{SAS_APP_URL}/indexView.html?iiif-content={obj.gen_manifest_url(version=MANIFEST_V2)}"
    elif action == "similarity":
        color = "#24d1b7"
        icon = get_icon("code-compare")
        link = f"{APP_URL}/{APP_NAME}/{obj.get_ref()}/show-similarity"
    elif action == "regions":
        color = "#008CBA"
        icon = get_icon("eye")
        link = f"{APP_URL}/{APP_NAME}/{obj.get_ref()}/show-all-regions"
    elif action == "vectors":
        color = "#EFB80B"
        icon = get_icon("arrows")
        link = f"{APP_URL}/{APP_NAME}/{obj.get_ref()}/show-vectorization"
    elif action == "vectorization":
        color = "#EFB80B"
        icon = get_icon("pen-to-square")
        link = f"{APP_URL}/{APP_NAME}/run-vectorization/{obj.get_ref()}"
    else:
        # When the button is not supposed to redirects to anything
        link = "#"
        btn = get_action(action, "upper")
        color = "#878787"
        icon = get_icon("eye-slash")
        disabled = "disabled"

    return (
        f"<a href='{link}' class='btn btn-md active manifest-regions' role='button' aria-pressed='true' target='_blank'"
        f"{disabled} style='background-color:{color};'>{icon} {btn}</a>"
    )


def get_link_manifest(obj, version=None):
    """
    obj: Regions | Digitization
    """
    manifest_url = obj.gen_manifest_url(version=version)
    return f"<a id='{obj.get_ref()}' href='{manifest_url}' target='_blank'>{manifest_url} {IIIF_ICON}</a>"


def gen_btn(obj, action="view"):
    """
    obj: Regions | Digitization
    """
    if action == "no_manifest" or action == "no_regions" or action == "no_digit":
        return mark_safe(regions_btn(obj, action))

    is_regions = True
    if action == "regions" or action == "vectors":
        return mark_safe(f"<br>{regions_btn(obj, action)}")

    if action == "auto-view":
        digit_id = obj.id if cls(obj) == Digitization else obj.get_digit().id
        download_url = f"{APP_URL}/{APP_NAME}/iiif/digit-regions/{digit_id}"
        regions_type = "TXT"
        version = None if cls(obj) == Digitization else MANIFEST_V1
        is_regions = obj.has_regions() if cls(obj) == Digitization else True
    else:
        download_url = f"{SAS_APP_URL}/search-api/{obj.get_ref()}/search/"
        regions_type = "JSON"
        version = MANIFEST_V2
    # else:
    #     return mark_safe("NOT SUPPOSED TO OCCUR")

    download = (
        f'<a href="{download_url}" target="_blank">{get_icon("download")} {get_action("download")} ({regions_type})</a>'
        if is_regions
        else ""
    )

    return mark_safe(
        # todo: do a method of Regions and Digitization instead?
        f"{get_link_manifest(obj, version)}<br>{regions_btn(obj, action)}<br>{download}"
    )


def gen_manifest_btn(digit: Digitization, has_manifest=True, inline=False):
    manifest = digit.gen_manifest_url()
    mf = (
        f"<a href='{manifest}' target='_blank'>{IIIF_ICON}</a>"
        if has_manifest
        else f"<a href='{manifest}' class='disabled' disabled>{IIIF_ICON}</a>"
        # else f"<span class='faded'>{get_action('no_manifest')}</span>"
    )
    if inline:
        return mark_safe(mf)
    return mark_safe(f"<div class='iiif-icon'>{mf}</div>")
