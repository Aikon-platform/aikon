from dal import autocomplete
import django_filters
from django.forms import DateTimeField, DateField
from django.forms.models import ModelChoiceIteratorValue

from app.webapp.models.edition import Edition, get_name as edition_name
from app.webapp.models.language import Language
from app.webapp.models.witness import Witness, get_name as witness_name
from app.webapp.models.work import get_name as work_name


def serialize_choice_value(value):
    if isinstance(value, ModelChoiceIteratorValue):
        return str(value.value)
    return value


class RecordFilter(django_filters.FilterSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_labels = getattr(self.Meta, "labels", {})

    def to_form_fields(self):
        form_fields = []

        for field_name, field in self.form.fields.items():
            label = self.custom_labels.get(field_name.replace("__icontains", ""))

            field_info = {
                "name": field_name,
                "type": field.__class__.__name__,
                "label": label or field.label,
                "required": field.required,
                "help_text": field.help_text,
                "initial": field.initial,
            }

            if hasattr(field, "choices"):
                field_info["choices"] = [
                    {"value": serialize_choice_value(choice[0]), "label": choice[1]}
                    for choice in field.choices
                ]

            if isinstance(field, (DateTimeField, DateField)):
                field_info["initial"] = (
                    field.initial.isoformat() if field.initial else None
                )

            form_fields.append(field_info)

        return form_fields


class WitnessFilter(RecordFilter):
    # TODO make autocompletion work
    edition = django_filters.ModelChoiceFilter(
        queryset=Edition.objects.all(),
        widget=autocomplete.ModelSelect2(url="webapp:edition-autocomplete"),
    )
    contents__lang = django_filters.ModelChoiceFilter(
        queryset=Language.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(url="webapp:language-autocomplete"),
    )
    contents__date_min = django_filters.RangeFilter(
        field_name="contents__date_min", label=witness_name("date_min")
    )  # , widget=django_filters.widgets.RangeWidget(attrs={"class": "range"}))
    contents__date_max = django_filters.RangeFilter(
        field_name="contents__date_max", label=witness_name("date_max")
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
        labels = {
            "type": witness_name("type"),
            "id_nb": witness_name("id_nb"),
            "place": witness_name("ConservationPlace"),
            "edition": edition_name("Edition"),
            "edition__name": edition_name("name"),
            "edition__place": edition_name("pub_place"),
            "edition__publisher": edition_name("publisher"),
            "contents__work": work_name("Work"),
            "contents__work__title": work_name("title"),
            "contents__work__author": work_name("author"),
            "contents__lang": witness_name("Language"),
            "contents__tags": witness_name("Tag"),
        }
