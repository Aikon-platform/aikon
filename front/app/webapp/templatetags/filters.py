from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.forms import Textarea, SelectMultiple, Select, TypedChoiceField, BoundField
from django.template import Library
from app.config.settings import CANTALOUPE_APP_URL, SAS_APP_URL, APP_URL, APP_NAME
from app.webapp.utils.constants import MANIFEST_V2, TRUNCATEWORDS_SIM
import pprint
import json

from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.urls import NoReverseMatch, reverse

# from django.forms.widgets import Select

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
def ref_to_mirador(regions_refs, img_ref):
    # img_ref = {img_name}_{coord} / e.g. "wit205_pdf216_021_667,1853,783,412"
    img_ref = img_ref.split("_")
    digit_ref = "_".join(img_ref[0:1])

    regions_ref = [ref for ref in regions_refs if ref.startswith(digit_ref)][0]
    manifest = f"{APP_URL}/{APP_NAME}/iiif/{MANIFEST_V2}/{regions_ref}/manifest.json"

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


@register.filter
def truncate_words(text, max_length=TRUNCATEWORDS_SIM):
    words = text.split()
    if len(words) > 2 * max_length:  # Check if the text is longer than 2*TRUNCATEWORDS
        return " ".join(words[:max_length] + ["..."] + words[-max_length:])
    return text


@register.filter
def jpg_to_none(img_file):
    return img_file.replace(".jpg", "")


@register.filter
def add_str(arg1, arg2):
    return str(arg1) + str(arg2)


@register.filter
def model_name(obj):
    return obj.__class__.__name__


@register.filter
def dump(obj):
    return mark_safe(f"<pre>{escape(pprint.pformat(vars(obj), indent=4))}</pre>")


@register.filter
def js(obj):
    return json.dumps(obj)


@register.simple_tag
def get_url(entity, action="add"):
    """
    Generate an add URL for an entity by checking multiple URL patterns.
    Returns the first valid URL or an empty string if none found.
    """
    webapp_action = "create" if action == "add" else "list"
    url_patterns = [
        f"webapp:{entity}_{webapp_action}",
        f"admin:webapp_{entity}_{action}",
        f"admin:auth_{entity}_{action}",
    ]

    for pattern in url_patterns:
        url = check_url(pattern)
        if url:
            return url
    return ""


@register.simple_tag
def get_add_url(entity):
    return get_url(entity, "add")


@register.simple_tag
def get_list_url(entity):
    return get_url(entity, "changelist")


@register.simple_tag
def check_url(*args, **kwargs):
    try:
        return reverse(*args, **kwargs)
    except NoReverseMatch:
        return ""
    except Exception:
        return ""


@register.filter
def field_type(obj):
    return obj.field.widget.__class__.__name__


@register.filter
def is_select(field):
    if not hasattr(field, "field"):
        return False

    return isinstance(field.field.widget, Select)


@register.filter
def get_field_type(field):
    if not hasattr(field, "field"):
        return "default"
    if not isinstance(field, BoundField):
        return "default"

    widget = field.field.widget
    if isinstance(widget, SelectMultiple):
        return "multiselect"
    elif isinstance(widget, Select):
        return "select"
    elif isinstance(widget, Textarea):
        return "textarea"
    elif isinstance(widget, RelatedFieldWidgetWrapper):
        if "multiple>" in str(field):
            return "multiselect"
        return "default"
    else:
        return "default"
