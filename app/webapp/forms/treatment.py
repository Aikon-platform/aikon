from dal import autocomplete
from django import forms

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
