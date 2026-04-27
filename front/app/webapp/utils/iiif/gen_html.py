from django.utils.safestring import mark_safe

from django.urls import reverse
from app.webapp.models.digitization import Digitization
from app.webapp.utils.functions import get_icon, get_action, cls
from app.config.settings import (
    MIRADOR_BASE_URL,
    AIIINOTATE_BASE_URL,
    APP_URL,
    APP_NAME,
    APP_LANG,
)
from app.webapp.utils.iiif import IIIF_ICON


def regions_btn(obj, action="view"):
    """
    TODO check if still used
    obj: Regions | Digitization
    """
    disabled = ""
    btn = f"{get_action(action, 'upper')}"

    if action == "view":
        icon = get_icon("eye")
        # The link redirects to Mirador with no regions (Digitization) or automatic regions (Regions)
        link = f"{MIRADOR_BASE_URL}/index.html?iiif-content={obj.get_manifest_url()}"
    elif action == "auto-view":
        icon = get_icon("eye")
        # The link redirects to Mirador with no regions (Digitization) or automatic regions (Regions)
        link = f"{MIRADOR_BASE_URL}/index.html?iiif-content={obj.get_manifest_url()}"
    # elif action == "edit":
    #     icon = get_icon("pen-to-square")
    #     # The link redirects to the edit regions page (show_regions() view DELETED)
    #     link = f"{APP_URL}/{APP_NAME}/{obj.get_ref()}/show/"
    elif action == "final":
        icon = get_icon("check")
        # The link redirects to Mirador with corrected regions (Regions)
        link = f"{MIRADOR_BASE_URL}/index.html?iiif-content={obj.get_manifest_url()}"
    # elif action == "similarity":
    #     icon = get_icon("code-compare")
    #     link = f"{APP_URL}/{APP_NAME}/{obj.get_ref()}/show-similarity"
    elif action == "regions":
        icon = get_icon("eye")
        link = f"{APP_URL}/{APP_NAME}/{obj.get_ref()}/show-all-regions"
    elif action == "vectors":
        icon = get_icon("arrows")
        link = f"{APP_URL}/{APP_NAME}/{obj.get_ref()}/show-vectorization"
    elif action == "vectorization":
        icon = get_icon("pen-to-square")
        link = f"{APP_URL}/{APP_NAME}/run-vectorization/{obj.get_ref()}"
    else:
        # When the button is not supposed to redirect to anything
        link = "#"
        btn = get_action(action, "upper")
        icon = get_icon("eye-slash")
        disabled = "disabled"

    return (
        f"<a href='{link}' class='button active is-link is-small my-2' role='button' "
        f"aria-pressed='true' target='_blank' {disabled}>{icon} {btn}</a>"
    )


def get_link_manifest(obj):
    """
    obj: Regions | Digitization
    """
    manifest_url = obj.get_manifest_url()
    return f"<a id='{obj.get_ref()}' href='{manifest_url}' target='_blank'>{manifest_url} {IIIF_ICON}</a>"


def gen_btn(obj, action="view"):
    """
    obj: Regions | Digitization
    """
    if action == "no_manifest" or action == "no_regions" or action == "no_digit":
        return mark_safe(regions_btn(obj, action))

    is_regions = True
    if action == "regions":
        region_url = reverse(
            "webapp:regions_view", kwargs={"wid": obj.get_witness().id, "rid": obj.id}
        )
        title = "Show regions" if APP_LANG == "en" else "Afficher les régions"
        return mark_safe(
            f"<a href='{region_url}' class='button is-small is-link px-2' title='{title}'>"
            f"<span class='iconify' data-icon='entypo:documents'/>"
            f"<span class='ml-2'>{title.upper()}</span></a>"
        )
    download_url = f"{AIIINOTATE_BASE_URL}/search-api/2/{obj.get_ref()}/search/"
    regions_type = "JSON"

    download = (
        f'<a href="{download_url}" target="_blank">{get_icon("download")} {get_action("download")} ({regions_type})</a>'
        if is_regions
        else ""
    )

    return mark_safe(
        # todo: do a method of Regions and Digitization instead?
        f"{get_link_manifest(obj)}<br>{regions_btn(obj, action)}<br>{download}"
    )


def gen_manifest_btn(digit: Digitization, has_manifest=True, inline=False):
    manifest = digit.get_manifest_url()
    mf = (
        f"<a href='{manifest}' target='_blank'>{IIIF_ICON}</a>"
        if has_manifest
        else f"<a href='{manifest}' class='disabled' disabled>{IIIF_ICON}</a>"
        # else f"<span class='faded'>{get_action('no_manifest')}</span>"
    )
    if inline:
        return mark_safe(mf)
    return mark_safe(f"<div class='iiif-icon'>{mf}</div>")
