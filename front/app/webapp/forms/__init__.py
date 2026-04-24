# TODO! create forms for main entities
from app.webapp.forms.forms import *
from app.webapp.forms.witness import *


class InputSourceForm(forms.Form):
    INPUT_SOURCES = [
        ("regions", "Extracted Regions" if APP_LANG == "en" else "Régions extraites"),
        # ("regions_model", "Extracted Regions (specific model)"),  # TODO: implement model filtering
        ("pages", "Full Page Images" if APP_LANG == "en" else "Images pleine page"),
    ]

    # TODO uncomment to allow executing task on full page images (notably similarity)
    # TODO for now the issue is that the svelte witness/similarity page is designed to work with regions
    # see https://trello.com/c/kxk6MpUb/302
    # source_type = forms.ChoiceField(
    #     choices=INPUT_SOURCES,
    #     initial="regions",
    #     label="Input Source" if APP_LANG == "en" else "Source d'entrée",
    #     widget=forms.RadioSelect,
    # )

    # source_model = forms.ChoiceField(
    #     required=False,
    #     label="Extraction Model",
    #     choices=[],  # Populated dynamically
    #     widget=forms.Select(attrs={"extra-class": "source-model-field"}),
    # )
