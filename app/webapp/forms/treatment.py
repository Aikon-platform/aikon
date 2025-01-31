from dal import autocomplete
from django import forms

from app.config.settings import CV_API_URL, APP_LANG, INSTALLED_APPS
from app.webapp.forms import SEARCH_MSG
from app.webapp.models.treatment import Treatment


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

        for task in INSTALLED_APPS:
            if task == "similarity":
                self.add_similarity_form()
            elif task == "regions":
                self.add_regions_form()
            elif task == "vectorization":
                self.add_vectorization_form()

    def _populate_instance(self, instance):
        instance.requested_by = self._user

    def save(self, commit=True):
        instance = super().save(commit=False)
        self._populate_instance(instance)

        if commit:
            instance.save()

        return instance

    def add_similarity_form(self):
        pass

    def add_regions_form(self):
        pass

    def add_vectorization_form(self):
        pass
