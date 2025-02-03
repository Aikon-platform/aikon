from django import forms

from app.config.settings import APP_LANG
from app.vectorization.const import MODULE_NAME
from app.webapp.forms import get_available_models


class VectorizationForm(forms.Form):
    class Meta:
        fields = ("model",)

    model = forms.ChoiceField(
        label="Model",
        help_text=(
            "Model used to vectorize the images regions"
            if APP_LANG == "en"
            else "Modèle pour vectoriser les régions d'images"
        ),
        choices=[],  # dynamically set in __init__
        widget=forms.RadioSelect,
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["model"].choices = get_available_models(MODULE_NAME)

    def get_api_parameters(self):
        parameters = {"model": self.cleaned_data["model"]}
        return parameters
