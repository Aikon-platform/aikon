from dal import autocomplete
from django import forms

from app.config.settings import ADDITIONAL_MODULES
from app.similarity.forms import SimilarityForm
from app.regionextraction.forms import RegionExtractionForm
from app.vectorization.forms import VectorizationForm
from app.webapp.forms import SEARCH_MSG
from app.webapp.models.treatment import Treatment
from app.webapp.models.utils.constants import TRMT_TYPE


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
        self._document_set = kwargs.pop("document_set", None)
        self._task_type = kwargs.pop("task_type", None)
        self._notify_email = kwargs.pop("notify_email", None)

        super().__init__(*args, **kwargs)

        self.fields["task_type"].choices = (("", "-"),) + TRMT_TYPE

        self.subforms = {}
        form_mapping = {
            "similarity": SimilarityForm,
            "regions": RegionExtractionForm,
            "vectorization": VectorizationForm,
        }

        for task_name in ADDITIONAL_MODULES:
            if task_name in form_mapping:
                self.add_subform(
                    task_name,
                    form_mapping[task_name],
                    kwargs.get("data"),
                    kwargs.get("files"),
                )

        self._prefill()

    def _prefill(self):
        if self._document_set:
            self.initial["document_set"] = self._document_set
        if self._task_type:
            self.initial["task_type"] = self._task_type
        if self._notify_email:
            self.initial["notify_email"] = self._notify_email.lower() == "true"

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
                name.replace(f"{prefix}_", ""): value
                for name, value in data.items()
                if name.startswith(f"{prefix}_")
            }

        self.subforms[prefix] = form_class(
            data=subform_data,
            prefix=prefix,
            files=files,
        )
        for name, field in self.subforms[prefix].fields.items():
            field.required = False  # make it optional and validate inside subforms
            self.fields[f"{prefix}_{name}"] = field

    def clean(self):
        cleaned_data = super().clean()

        if not cleaned_data.get("document_set"):
            self.add_error("document_set", "A document set is required.")

        task_type = cleaned_data.get("task_type")
        if not task_type:
            self.add_error("task_type", "A task type is required.")

        subform = self.subforms.get(task_type)
        # Only validate selected subtask form
        if not subform.is_valid():
            for field, error in subform.errors.items():
                self.add_error(f"{task_type}_{field}", error)
        # else:
        #     # If subform clean() method are modifying the data, uncomment
        #     cleaned_data.update(
        #         {f"{task_type}_{k}": v for k, v in subform.cleaned_data.items()}
        #     )
        return cleaned_data
