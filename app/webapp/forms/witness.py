from django import forms

# from app.webapp.admin import DigitizationInline, ContentInline
from app.webapp.models.witness import Witness


class WitnessForm(forms.ModelForm):
    class Meta:
        model = Witness
        fields = [
            "type",
            "id_nb",
            "place",
            "page_type",
            "nb_pages",
            "notes",
            "edition",
            "volume_nb",
            "volume_title",
            "link",
            "is_public",
        ]

    # inlines = [DigitizationInline, ContentInline]
