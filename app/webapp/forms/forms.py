import requests
from dataclasses import dataclass
from typing import Type

from django import forms
from dal import autocomplete

from app.config.settings import APP_LANG, CV_API_URL
from app.webapp.models.language import Language
from app.webapp.models.place import Place


SEARCH_MSG = "Search..." if APP_LANG == "en" else "Rechercher..."


@dataclass
class FormConfig:
    display_name: str
    description: str
    form_class: Type[forms.Form]


class SubForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields = {
            f"{self.prefix}{name}": field for name, field in self.fields.items()
        }


def get_available_models(task_name):
    try:
        response = requests.get(f"{CV_API_URL}/{task_name}/models")
        response.raise_for_status()
        models = response.json()
    except Exception as e:
        fetch_error = (
            f"Unable to fetch available models: {e}"
            if APP_LANG == "en"
            else f"Impossible de récupérer les modèles disponibles : {e}"
        )
        return [("", fetch_error)]
    if not models:
        return [
            (
                "",
                "No available models"
                if APP_LANG == "en"
                else "Aucun modèle disponible",
            )
        ]

    # models = { "ref": { "name": "Display Name", "model": "filename", "desc": "Description" }, ... }
    return [
        (info["model"], f"{info['name']} ({info['desc']})") for info in models.values()
    ]


class PlaceForm(forms.ModelForm):
    class Meta:
        model = Place
        fields = "__all__"
        widgets = {
            "name": autocomplete.ListSelect2(
                url="webapp:place-autocomplete",
                attrs={
                    "data-placeholder": SEARCH_MSG,
                },
                # forward=["name"],
            ),
            "country": forms.TextInput(attrs={"readonly": "readonly"}),
            "latitude": forms.TextInput(attrs={"readonly": "readonly"}),
            "longitude": forms.TextInput(attrs={"readonly": "readonly"}),
        }

    def __init__(self, *args, **kwargs):
        super(PlaceForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.name:
            self.fields["name"].widget.choices = [
                (self.instance.name, self.instance.name)
            ]

    class Media:
        js = ("js/place-autocomplete.js",)


class LanguageForm(forms.ModelForm):
    class Meta:
        model = Language
        fields = "__all__"
        widgets = {
            "lang": autocomplete.ModelSelect2Multiple(
                url="webapp:language-autocomplete",
                attrs={
                    "data-placeholder": SEARCH_MSG,
                },
            ),
        }

    def __init__(self, *args, **kwargs):
        super(LanguageForm, self).__init__(*args, **kwargs)
        # self.fields["lang"].help_text = None  # Set help_text to None to remove it
