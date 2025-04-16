from dal import autocomplete
from django.db.models import Q
from django.forms import DateTimeField, DateField
from django_filters import FilterSet
from django_filters.filters import (
    ModelChoiceFilter,
    ModelMultipleChoiceFilter,
    RangeFilter,
    CharFilter,
    OrderingFilter,
)
from django.forms.models import ModelChoiceIteratorValue

from app.config.settings import APP_LANG
from app.webapp.models.conservation_place import ConservationPlace
from app.webapp.models.digitization import Digitization, get_name as digitization_name
from app.webapp.models.document_set import DocumentSet
from app.webapp.models.edition import Edition, get_name as edition_name
from app.webapp.models.language import Language
from app.webapp.models.person import Person
from app.webapp.models.place import Place
from app.webapp.models.regions import Regions
from app.webapp.models.series import Series, get_name as series_name
from app.webapp.models.tag import Tag
from app.webapp.models.treatment import Treatment, get_name as treatment_name
from app.webapp.models.witness import Witness, get_name as witness_name
from app.webapp.models.work import Work, get_name as work_name

QS_MODELS = {
    "edition": Edition,
    "contents__work": Work,
    "contents__tags": Tag,
    "contents__work__author": Person,
    "edition__place": Place,
    "edition__publisher": Person,
    "place": ConservationPlace,
    "contents__lang": Language,
    "work": Work,
    "wit_ids": Witness,
    "ser_ids": Series,
    "work_ids": Work,
}


class RecordFilter(FilterSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_labels = getattr(self.Meta, "labels", {})
        self.search_fields = ["json"]
        self.filters["search"] = self.create_search_filter()

        # if not hasattr(self, 'ordering'):
        #     ordering_fields = getattr(self.Meta, "ordering_fields", ["updated_at", "-updated_at"])
        #     ordering_labels = getattr(self.Meta, "ordering_labels", {
        #         "updated_at": "Modification Date (oldest first)" if APP_LANG == "en" else "Date de modification (plus ancien)",
        #         "-updated_at": "Modification Date (newest first)" if APP_LANG == "en" else "Date de modification (plus récent)",
        #     })
        #
        #     self.filters["ordering"] = OrderingFilter(
        #         fields=ordering_fields,
        #         field_labels=ordering_labels,
        #         label="Sort by" if APP_LANG == "en" else "Trier par",
        #     )
        if hasattr(self, "queryset") and hasattr(self.queryset.model, "updated_at"):
            self.queryset = self.queryset.order_by("-updated_at")

    @staticmethod
    def get_choices(model):
        """
        Get an efficient list of choices for any model.

        :param model: The Django model class
        :return: [{"value": record.id, "label": record.str()}, {"value": record.id, "label": record.str()}, ... ]
        """
        queryset = model.objects.all()

        data = list(queryset.values(*("id",)))
        for item, obj in zip(data, list(queryset)):
            item["label"] = obj.__str__(light=True)

        data.insert(0, {"id": "", "label": "----------"})
        return data

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
                if field_name in QS_MODELS:
                    field_info["choices"] = self.get_choices(QS_MODELS[field_name])
                else:
                    field_info["choices"] = [
                        {"id": self.get_val(choice[0]), "label": str(choice[1])}
                        for choice in field.choices
                    ]

            if isinstance(field, (DateTimeField, DateField)):
                field_info["initial"] = (
                    field.initial.isoformat() if field.initial else None
                )

            form_fields.append(field_info)

        return form_fields

    def create_search_filter(self):
        return CharFilter(
            method=self.search_method,
            label="Full-text search" if APP_LANG == "en" else "Recherche plein texte",
        )

    def search_method(self, queryset, name, value):
        if value and self.search_fields:
            q_objects = Q()
            for field in self.search_fields:
                q_objects |= Q(**{f"{field}__icontains": value})
            return queryset.filter(q_objects)
        return queryset

    @staticmethod
    def get_val(value):
        if isinstance(value, ModelChoiceIteratorValue):
            return str(value.value)
        return value


class WitnessFilter(RecordFilter):
    edition = ModelChoiceFilter(
        queryset=Edition.objects.all(),
    )
    contents__work = ModelChoiceFilter(
        queryset=Work.objects.all(),
    )
    contents__work__author = ModelChoiceFilter(
        queryset=Person.objects.all(),
    )
    place = ModelChoiceFilter(
        queryset=ConservationPlace.objects.all(),
    )
    # series = ModelChoiceFilter(
    #     queryset=Series.objects.all(),
    # )
    contents__lang = ModelMultipleChoiceFilter(
        queryset=Language.objects.all(),
        null_value=None,
    )
    contents__tags = ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        null_value=None,
    )
    contents__date_min = RangeFilter(
        field_name="contents__date_min", label=witness_name("date_min")
    )
    contents__date_max = RangeFilter(
        field_name="contents__date_max", label=witness_name("date_max")
    )

    class Meta:
        model = Witness
        fields = {
            "type": ["exact"],
            "id_nb": ["icontains"],
            "place": ["exact"],
            "edition": ["exact"],
            # "series": ["exact"],
            "contents__work": ["exact"],
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
            # "series": series_name("Series"),
            "contents__work": work_name("Work"),
            "contents__work__title": work_name("title"),
            "contents__work__author": work_name("author"),
            "contents__lang": witness_name("Language"),
            "contents__tags": witness_name("Tag"),
        }


class TreatmentFilter(RecordFilter):
    class Meta:
        model = Treatment
        fields = {
            "status": ["exact"],
            "task_type": ["exact"],
        }
        labels = {
            "status": treatment_name("status"),
            "task_type": treatment_name("task_type"),
        }


class WorkFilter(RecordFilter):
    contents__lang = ModelChoiceFilter(
        queryset=Language.objects.all(),
    )
    contents__date_min = RangeFilter(
        field_name="contents__date_min", label=witness_name("date_min")
    )
    contents__date_max = RangeFilter(
        field_name="contents__date_max", label=witness_name("date_max")
    )

    class Meta:
        model = Work
        fields = {
            # "place": ["exact"],
            "author": ["exact"],
        }
        labels = {
            "place": work_name("place"),
            "author": work_name("author"),
            "contents__lang": work_name("Language"),
        }


class SeriesFilter(RecordFilter):
    edition = ModelChoiceFilter(
        queryset=Edition.objects.all(),
    )
    edition__place = ModelChoiceFilter(
        queryset=Place.objects.all(),
    )
    edition__publisher = ModelChoiceFilter(
        queryset=Person.objects.all(),
    )
    contents__date_min = RangeFilter(
        field_name="contents__date_min", label=witness_name("date_min")
    )
    contents__date_max = RangeFilter(
        field_name="contents__date_max", label=witness_name("date_max")
    )

    class Meta:
        model = Series
        fields = {
            "edition": ["exact"],
            "edition__name": ["exact"],
            "edition__place": ["exact"],
            "edition__publisher": ["exact"],
        }
        labels = {
            "edition": edition_name("Edition"),
            "edition__name": edition_name("name"),
            "edition__place": edition_name("pub_place"),
            "edition__publisher": edition_name("publisher"),
        }


class DocumentSetFilter(RecordFilter):
    wit_ids = ModelMultipleChoiceFilter(
        queryset=Witness.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(url="witness-autocomplete"),
        method="filter_by_witness",
        null_value=None,
        null_label="----------",
        label=witness_name("Witness"),
    )
    ser_ids = ModelMultipleChoiceFilter(
        queryset=Series.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(url="series-autocomplete"),
        method="filter_by_series",
        null_value=None,
        null_label="----------",
        label=series_name("Series"),
    )
    work_ids = ModelMultipleChoiceFilter(
        queryset=Work.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(url="work-autocomplete"),
        method="filter_by_work",
        null_value=None,
        null_label="----------",
        label=work_name("Work"),
    )

    class Meta:
        model = DocumentSet
        fields = {
            "title": ["icontains"],
        }
        labels = {
            "title": work_name("title"),
        }

    def filter_by_witness(self, queryset, name, value):
        if value:
            wit_ids = [w.id for w in value]
            return queryset.filter(wit_ids__overlap=wit_ids)
        return queryset

    def filter_by_series(self, queryset, name, value):
        if value:
            ser_ids = [s.id for s in value]
            return queryset.filter(ser_ids__overlap=ser_ids)
        return queryset

    def filter_by_work(self, queryset, name, value):
        if value:
            work_ids = [w.id for w in value]
            return queryset.filter(work_ids__overlap=work_ids)
        return queryset


class DigitizationFilter(RecordFilter):
    witness = ModelChoiceFilter(
        queryset=Witness.objects.all(),
    )

    class Meta:
        model = Digitization
        fields = {
            "witness": ["exact"],
            "is_open": ["exact"],
            "digit_type": ["exact"],
        }
        labels = {
            "witness": digitization_name("Witness"),
            "is_open": digitization_name("is_open"),
            "digit_type": digitization_name("type"),
        }


class RegionsFilter(RecordFilter):
    digitization = ModelChoiceFilter(
        queryset=Digitization.objects.all(),
    )

    class Meta:
        model = Regions
        fields = {
            "digitization": ["exact"],
        }
