from django import forms

from app.config.settings import APP_LANG
from app.regionextraction.const import MODULE_NAME
from app.webapp.forms import get_available_models

DEFAULT_MODEL = "illustration_extraction"


class RegionExtractionForm(forms.Form):
    class Meta:
        fields = ("model",)

    model = forms.ChoiceField(
        label="Model",
        help_text=(
            "Model used to extract image regions in the document set"
            if APP_LANG == "en"
            else "Modèle pour extraire des régions d'image dans le set de documents"
        ),
        choices=[("", "-")],  # dynamically set in __init__
        initial=DEFAULT_MODEL,  # if not available, will default to first in list
        # widget=forms.RadioSelect,
        required=True,
    )

    # NOTE for watermarks only
    # postprocess_watermarks = forms.BooleanField(
    #     label="Squarify and add 5% margin to crops",
    #     required=False,
    # )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["model"].choices = get_available_models(MODULE_NAME)

    def clean(self):
        cleaned_data = super().clean()
        if model := self.data.get("model"):
            cleaned_data["model"] = model
        else:
            self.add_error("model", "Select a model to extract image regions")
        return cleaned_data

    def get_api_parameters(self):
        parameters = {"model": self.cleaned_data.get("model")}
        # NOTE for watermarks only
        # if self.cleaned_data.get("postprocess_watermarks"):
        #     parameters["postprocess"] = "watermarks"
        return parameters
