from django.template import Library
from app.config.settings import CANTALOUPE_APP_URL, SAS_APP_URL, APP_URL, APP_NAME
from app.webapp.utils.constants import MANIFEST_V1, MANIFEST_V2

register = Library()


@register.filter
def range_filter(value):
    """
    Generate a range of numbers
    """
    return range(value)


@register.filter
def split(value, sep):
    """
    Split a string by a separator and return a list
    """
    return value.split(sep)


@register.filter
def replace_nth_part_of_url(url, args):
    """
    Replace a specific component of a URL string
    """
    new_part, n = args.split(";")
    n = int(n)
    parts = url.split("/")
    parts[n] = new_part
    return "/".join(parts)


@register.filter
def img_to_iiif(img_file, args="full/full/0"):
    # args = {region}/{size}/{orientation}
    return f"{CANTALOUPE_APP_URL}/iiif/2/{img_file}/{args}/default.jpg"


@register.filter
def ref_to_iiif(img_ref):
    # img_ref = {img_name}_{coord} / e.g. "wit205_pdf216_021_667,1853,783,412"
    img_ref = img_ref.split("_")
    img_name, img_coord = "_".join(img_ref[:-1]), img_ref[-1]
    return f"{CANTALOUPE_APP_URL}/iiif/2/{img_name}.jpg/{img_coord}/default.jpg"


@register.filter
def ref_to_mirador(anno_refs, img_ref):
    # img_ref = {img_name}_{coord} / e.g. "wit205_pdf216_021_667,1853,783,412"
    img_ref = img_ref.split("_")
    digit_ref = "_".join(img_ref[0:1])

    anno_ref = [ref for ref in anno_refs if ref.startswith(digit_ref)][0]
    manifest = f"{APP_URL}/{APP_NAME}/iiif/{MANIFEST_V2}/{anno_ref}/manifest.json"

    return f"{SAS_APP_URL}/index.html?iiif-content={manifest}&canvas={int(img_ref[-2])}"


@register.filter
def exclude_and_join(lst, item):
    """
    Exclude a specific item from a list and join the remaining items with underscores
    """
    return "_".join(str(i) for i in lst if i != item)


@register.filter
def exclude_item_from_list(lst, item):
    """
    Exclude a specific item from a list and return the remaining items
    """
    return [i for i in lst if i != item]
