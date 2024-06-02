import django_filters
from dal import autocomplete
from django.template import Library
from app.config.settings import CANTALOUPE_APP_URL, SAS_APP_URL, APP_URL, APP_NAME
from app.webapp.models.edition import Edition
from app.webapp.models.language import Language
from app.webapp.models.witness import Witness
from app.webapp.utils.constants import MANIFEST_V2, TRUNCATEWORDS_SIM

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


@register.filter
def truncate_words(text, max_length=TRUNCATEWORDS_SIM):
    words = text.split()
    if len(words) > 2 * max_length:  # Check if the text is longer than 2*TRUNCATEWORDS
        return " ".join(words[:max_length] + ["..."] + words[-max_length:])
    return text


@register.filter
def jpg_to_none(img_file):
    return img_file.replace(".jpg", "")


class WitnessFilter(django_filters.FilterSet):
    edition = django_filters.ModelChoiceFilter(
        queryset=Edition.objects.all(),
        widget=autocomplete.ModelSelect2(url="edition-autocomplete"),
    )
    contents__lang = django_filters.ModelChoiceFilter(
        queryset=Language.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(url="language-autocomplete"),
    )
    contents__date_min = django_filters.RangeFilter(
        field_name="contents__date_min", label="Date minimale"
    )  # , widget=django_filters.widgets.RangeWidget(attrs={"class": "range"}))
    contents__date_max = django_filters.RangeFilter(
        field_name="contents__date_max", label="Date maximale"
    )

    class Meta:
        model = Witness
        fields = {
            "type": ["exact"],
            "id_nb": ["icontains"],
            "place": ["exact"],
            "edition": ["exact"],
            "edition__name": ["exact"],
            "edition__place": ["exact"],
            "edition__publisher": ["exact"],
            "contents__work": ["exact"],
            "contents__work__title": ["exact"],
            "contents__work__author": ["exact"],
            "contents__lang": ["exact"],
            "contents__tags": ["exact"],
        }
