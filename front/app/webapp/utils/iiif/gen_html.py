from django.utils.safestring import mark_safe

from django.urls import reverse
from app.webapp.models.digitization import Digitization
from app.webapp.utils.constants import MANIFEST_V1, MANIFEST_V2
from app.webapp.utils.functions import get_icon, get_action, cls
from app.config.settings import (
    SAS_APP_URL,
    APP_URL,
    APP_NAME,
    APP_LANG,
)
from app.webapp.utils.iiif import IIIF_ICON


def region_extraction_btn(obj, action="view"):
    """
    obj: RegionExtraction | Digitization
    """
    disabled = ""
    btn = f"{get_action(action, 'upper')}"

    if action == "view":
        icon = get_icon("eye")
        # The link redirects to Mirador with no regions (Digitization) or automatic region extraction (RegionExtraction)
        link = f"{SAS_APP_URL}/indexView.html?iiif-content={obj.gen_manifest_url(version=MANIFEST_V1)}"
    elif action == "auto-view":
        icon = get_icon("eye")
        # The link redirects to Mirador with no regions (Digitization) or automatic region extraction (RegionExtraction)
        link = f"{SAS_APP_URL}/indexView.html?iiif-content={obj.gen_manifest_url(version=MANIFEST_V1)}"
    # elif action == "edit":
    #     icon = get_icon("pen-to-square")
    #     # The link redirects to the edit region extraction page (show_regions() view DELETED)
    #     link = f"{APP_URL}/{APP_NAME}/{obj.get_ref()}/show/"
    elif action == "final":
        icon = get_icon("check")
        # The link redirects to Mirador with corrected region extraction (RegionExtraction)
        link = f"{SAS_APP_URL}/indexView.html?iiif-content={obj.gen_manifest_url(version=MANIFEST_V2)}"
    # elif action == "similarity":
    #     icon = get_icon("code-compare")
    #     link = f"{APP_URL}/{APP_NAME}/{obj.get_ref()}/show-similarity"
    elif action == "region_extraction":
        icon = get_icon("eye")
        link = f"{APP_URL}/{APP_NAME}/{obj.get_ref()}/show-all-regions"
    elif action == "vectors":
        icon = get_icon("arrows")
        link = f"{APP_URL}/{APP_NAME}/{obj.get_ref()}/show-vectorization"
    elif action == "vectorization":
        icon = get_icon("pen-to-square")
        link = f"{APP_URL}/{APP_NAME}/run-vectorization/{obj.get_ref()}"
    else:
        # When the button is not supposed to redirects to anything
        link = "#"
        btn = get_action(action, "upper")
        icon = get_icon("eye-slash")
        disabled = "disabled"

    return (
        f"<a href='{link}' class='button active is-link is-small my-2' role='button' "
        f"aria-pressed='true' target='_blank' {disabled}>{icon} {btn}</a>"
    )


def get_link_manifest(obj, version=None):
    """
    obj: RegionExtraction | Digitization
    """
    manifest_url = obj.gen_manifest_url(version=version)
    return f"<a id='{obj.get_ref()}' href='{manifest_url}' target='_blank'>{manifest_url} {IIIF_ICON}</a>"


def gen_btn(obj, action="view"):
    """
    obj: RegionExtraction | Digitization
    """
    if (
        action == "no_manifest"
        or action == "no_region_extraction"
        or action == "no_digit"
    ):
        return mark_safe(region_extraction_btn(obj, action))

    is_region_extraction = True
    if action == "region_extraction":
        region_url = reverse(
            "webapp:region_extraction_view",
            kwargs={"wid": obj.get_witness().id, "rid": obj.id},
        )
        title = (
            "Show region extraction"
            if APP_LANG == "en"
            else "Afficher les régions extraites"
        )
        return mark_safe(
            f"<a href='{region_url}' class='button is-small is-link px-2' title='{title}'>"
            f"<span class='iconify' data-icon='entypo:documents'/>"
            f"<span class='ml-2'>{title.upper()}</span></a>"
        )
    # if action == "region_extraction" or action == "vectors":
    #     return mark_safe(f"<br>{region_extraction(obj, action)}")

    # if action == "auto-view":
    #     digit_id = obj.id if cls(obj) == Digitization else obj.get_digit().id
    #     download_url = f"{APP_URL}/{APP_NAME}/iiif/digit-regions/{digit_id}"
    #     region_extraction_type = "TXT"
    #     version = None if cls(obj) == Digitization else MANIFEST_V1
    #     is_region_extraction = obj.has_region_extractions() if cls(obj) == Digitization else True
    # else:
    #     download_url = f"{SAS_APP_URL}/search-api/{obj.get_ref()}/search/"
    #     region_extraction_type = "JSON"
    #     version = MANIFEST_V2
    # else:
    #     return mark_safe("NOT SUPPOSED TO OCCUR")
    download_url = f"{SAS_APP_URL}/search-api/{obj.get_ref()}/search/"
    region_extraction_type = "JSON"
    version = MANIFEST_V2

    download = (
        f'<a href="{download_url}" target="_blank">{get_icon("download")} {get_action("download")} ({region_extraction_type})</a>'
        if is_region_extraction
        else ""
    )

    return mark_safe(
        # todo: do a method of RegionExtraction and Digitization instead?
        f"{get_link_manifest(obj, version)}<br>{region_extraction_btn(obj, action)}<br>{download}"
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
