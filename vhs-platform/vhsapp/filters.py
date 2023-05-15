from django.template import Library
from vhs.settings import VHS_APP_URL, CANTALOUPE_APP_URL, SAS_APP_URL

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
