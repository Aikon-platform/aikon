from dal import autocomplete
from django import forms

from app.config.settings import ADDITIONAL_MODULES
from app.similarity.forms import SimilarityForm
from app.regions.forms import RegionsForm
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
        super().__init__(*args, **kwargs)
        self.fields["task_type"].choices = TRMT_TYPE

        self.subforms = {}
        form_mapping = {
            "similarity": SimilarityForm,
            "regions": RegionsForm,
            "vectorization": VectorizationForm,
        }

        for task in ADDITIONAL_MODULES:
            if task in form_mapping:
                self.add_subform(
                    task, form_mapping[task], kwargs.get("data"), kwargs.get("files")
                )

    def _populate_instance(self, instance):
        instance.requested_by = self._user

    def save(self, commit=True):
        instance = super().save(commit=False)
        self._populate_instance(instance)

        if commit:
            instance.save()

        return instance

    def add_subform(self, prefix, form_class, data=None, files=None):
        self.subforms[prefix] = form_class(
            {
                "prefix": prefix,
                "data": data,
                "files": files,
                "instance": getattr(self.instance, prefix, None),
            }
        )
        self.fields.update(
            {
                f"{prefix}_{name}": field
                for name, field in self.subforms[prefix].fields.items()
            }
        )

    def generate_api_parameters(self):
        # todo call get_api_parameter on selected task type associated form
        pass

    def clean(self):
        cleaned_data = super().clean()

        for prefix, subform in self.subforms.items():
            if not subform.is_valid():
                for field, error in subform.errors.items():
                    self.add_error(f"{prefix}_{field}", error)
            else:
                cleaned_data.update(
                    {f"{prefix}_{k}": v for k, v in subform.cleaned_data.items()}
                )
        return cleaned_data
