from dal import autocomplete
from django import forms

from app.config.settings import ADDITIONAL_MODULES
from app.similarity.forms import SimilarityForm
from app.region_extraction.forms import RegionExtractionForm
from app.similarity.remap import plan_path
from app.vectorization.forms import VectorizationForm
from app.webapp.forms import SEARCH_MSG, api_down
from app.webapp.models.treatment import Treatment
from app.webapp.models.utils.constants import TRMT_TYPE, LOCAL_TASKS, SUPERUSER_TASKS


class ImportForm(forms.Form):
    source_url = forms.URLField(
        label="Source URL",
        required=False,
        help_text="URL of a document set or witness JSON export from another AIKON instance "
        "(e.g. https://host/aikon/document-set/13/json)",
    )
    regions = forms.BooleanField(
        required=False, initial=True, label="Import region extractions"
    )
    similarities = forms.BooleanField(required=False, label="Import similarity pairs")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "similarity" not in ADDITIONAL_MODULES:
            del self.fields["similarities"]

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("source_url"):
            self.add_error("source_url", "A source URL is required.")
        return cleaned

    def get_api_parameters(self):
        return {
            "source_url": self.cleaned_data["source_url"],
            "import_regions": self.cleaned_data.get("regions", False),
            "import_similarities": self.cleaned_data.get("similarities", False),
        }


class TreatmentForm(forms.ModelForm):
    class Meta:
        model = Treatment
        fields = [
            "task_type",
            "document_set",
            "notify_email",
        ]

        widgets = {
            "document_set": autocomplete.ListSelect2(
                url="webapp:document-set-autocomplete",
                attrs={
                    "data-placeholder": SEARCH_MSG,
                },
            ),
        }

    def __init__(self, *args, **kwargs):
        self._user = kwargs.pop("user", None)
        self._prefill_data = kwargs.pop("prefill", {})

        super().__init__(*args, **kwargs)

        is_superuser = getattr(self._user, "is_superuser", False)
        self.fields["task_type"].choices = (("", "-"),) + tuple(
            t for t in TRMT_TYPE if is_superuser or t[0] not in SUPERUSER_TASKS
        )

        self.subforms = {}
        form_mapping = {
            "similarity": SimilarityForm,
            "region_extraction": RegionExtractionForm,
            "vectorization": VectorizationForm,
            "import": ImportForm,
        }

        for task_name in ADDITIONAL_MODULES + LOCAL_TASKS:
            if task_name in form_mapping:
                self.add_subform(
                    task_name,
                    form_mapping[task_name],
                    kwargs.get("data"),
                    kwargs.get("files"),
                )

        self.api_down = api_down()
        self.local_tasks = LOCAL_TASKS
        self._prefill()

    def _prefill(self):
        """Initial values from GET parameters, e.g. ?document_set=1&task_type=similarity&similarity_algorithm=cosine"""
        self.initial.update(
            {
                k: {"true": True, "false": False}.get(v.lower(), v)
                for k, v in self._prefill_data.items()
                if k in self.fields
            }
        )

    def _populate_instance(self, instance):
        instance.requested_by = self._user

        task_type = self.cleaned_data.get("task_type")
        if task_type in self.subforms:
            subform = self.subforms[task_type]
            if subform.is_valid():
                instance.api_parameters = subform.get_api_parameters()

    def save(self, commit=True):
        instance = super().save(commit=False)
        self._populate_instance(instance)

        if commit:
            instance.save()

        return instance

    def add_subform(self, prefix, form_class, data=None, files=None):
        subform_data = None
        if data:
            subform_data = {
                name.removeprefix(f"{prefix}_"): value
                for name, value in data.items()
                if name.startswith(f"{prefix}_")
            }

        self.subforms[prefix] = form_class(
            data=subform_data,
            files=files,
        )
        for name, field in self.subforms[prefix].fields.items():
            field.required = False  # make it optional and validate inside subforms
            self.fields[f"{prefix}_{name}"] = field

    def clean(self):
        cleaned_data = super().clean()

        task_type = cleaned_data.get("task_type")
        if not task_type:
            self.add_error("task_type", "A task type is required.")

        if not cleaned_data.get("document_set") and task_type != "import":
            self.add_error("document_set", "A document set is required.")

        if task_type not in LOCAL_TASKS and api_down():
            self.add_error("task_type", "The API is not responding, try again later.")

        doc_set = cleaned_data.get("document_set")
        if task_type == "remap" and doc_set and not plan_path(doc_set.id).exists():
            self.add_error("task_type", "Preview the remap before applying it.")

        subform = self.subforms.get(task_type)
        # Only validate selected subtask form
        if subform and not subform.is_valid():
            for field, error in subform.errors.items():
                self.add_error(f"{task_type}_{field}", error)
        # else:
        #     # If subform clean() method are modifying the data, uncomment
        #     cleaned_data.update(
        #         {f"{task_type}_{k}": v for k, v in subform.cleaned_data.items()}
        #     )
        return cleaned_data
