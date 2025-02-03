from django import forms

from app.config.settings import APP_LANG
from app.regions.const import MODULE_NAME
from app.webapp.forms import get_available_models


class RegionsForm(forms.Form):
    class Meta:
        fields = ("model",)

    model = forms.ChoiceField(
        label="Model",
        help_text=(
            "Model used to extract image regions in the document set"
            if APP_LANG == "en"
            else "Modèle pour extraire des régions d'image dans le set de documents"
        ),
        choices=[],  # dynamically set in __init__
        widget=forms.RadioSelect,
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

    def get_api_parameters(self):
        parameters = {"model": self.cleaned_data["model"]}
        # NOTE for watermarks only
        # if self.cleaned_data.get("postprocess_watermarks"):
        #     parameters["postprocess"] = "watermarks"
        return parameters
