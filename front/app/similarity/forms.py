from enum import Enum

from django import forms

from app.config.settings import APP_LANG
from app.similarity.const import MODULE_NAME
from app.webapp.forms import FormConfig, get_available_models, SubForm

AVAILABLE_SIMILARITY_ALGORITHMS = {
    "cosine": (
        "Similarity using cosine distance between feature vectors"
        if APP_LANG == "en"
        else "Similarité basée sur la distance cosinus entre les vecteurs de 'features'"
    ),
    "segswap": (
        "Similarity using correspondence matching between part of images"
        if APP_LANG == "en"
        else "Similarité basée sur la correspondance entre les parties des images"
    ),
}


class SimilarityForm(forms.Form):
    class Meta:
        fields = ("algorithm",)

    algorithm = forms.ChoiceField(
        choices=[("", "-")],  # Will be dynamically set in __init__
        initial="segswap",  # if segswap not available, will default to first in list
        label="Similarity Algorithm"
        if APP_LANG == "en"
        else "Algorithme de similarité",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.algorithm_forms = {}

        available_algos = [
            algo
            for algo in SimilarityAlgorithm
            if algo.name in AVAILABLE_SIMILARITY_ALGORITHMS
        ]

        self.fields["algorithm"].choices = [
            (algo.name, algo.config.display_name) for algo in available_algos
        ]

        for algo in available_algos:
            form = algo.config.form_class(
                **{"prefix": f"{algo.name}_", "data": kwargs.get("data")}
            )
            self.algorithm_forms[algo.name] = form
            self.fields.update(form.fields)

    def clean(self):
        cleaned_data = super().clean()
        algorithm = self.data.get("algorithm")
        if not algorithm:
            self.add_error("algorithm", "Please select a similarity algorithm")
            return cleaned_data
        cleaned_data["algorithm"] = algorithm

        algo_form = self.algorithm_forms[algorithm]
        if not algo_form.is_valid():
            for field, error in algo_form.errors.items():
                self.add_error(f"{algorithm}_{field}", error)
            return cleaned_data

        # cleaned_data.update(
        #     {f"{algorithm}_{field}": value for field, value in algo_form.data.items()}
        # )
        cleaned_data.update(
            {
                field: True if value == "on" else value
                for field, value in algo_form.data.items()
            }
        )
        return cleaned_data

    def get_api_parameters(self):
        algorithm = self.cleaned_data.get("algorithm")
        if not algorithm:
            return {}

        parameters = {}
        for name in self.algorithm_forms[algorithm].fields:
            api_param = name.replace(f"{algorithm}_", "")
            parameters[api_param] = self.cleaned_data.get(name)

        parameters["algorithm"] = algorithm

        # TODO make something more dynamic using AVAILABLE_SIMILARITY_ALGORITHMS
        if algorithm == "segswap":
            parameters.update(
                {
                    "segswap_prefilter": self.cleaned_data.get(
                        f"{algorithm}_cosine_preprocessing", True
                    ),
                    "segswap_n": self.cleaned_data.get(
                        f"{algorithm}_cosine_n_filter", 10
                    ),
                }
            )

        # NOTE for watermarks only
        # if parameters.get("use_transpositions"):
        #     parameters["transpositions"] = ["none", "rot90", "rot270", "hflip", "vflip"]

        return parameters


class BaseFeatureExtractionForm(forms.Form):
    """Base form for feature extraction settings."""

    class Meta:
        fields = ("feat_net",)

    feat_net = forms.ChoiceField(
        label="Feature Extraction Backbone"
        if APP_LANG == "en"
        else "Modèle d'extraction des 'features'",
        help_text=(
            "Select the model to extract main characteristics of the images on which to perform similarity"
            if APP_LANG == "en"
            else "Sélectionnez le modèle pour extraire les caractéristiques principales des images sur lesquelles effectuer la similarité"
        ),
        widget=forms.Select(attrs={"extra-class": "preprocessing-field"}),
    )

    # # NOTE NOT USED for now
    # cosine_threshold = forms.FloatField(
    #     min_value=0.1,
    #     max_value=0.99,
    #     initial=0.6,
    #     label="Cosine Threshold" if APP_LANG == "en" else "Seuil de Cosinus",
    #     widget=forms.NumberInput(attrs={"extra-class": "preprocessing-field"}),
    # )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["feat_net"].choices = get_available_models(MODULE_NAME)


class CosinePreprocessing(BaseFeatureExtractionForm):
    """Form for SegSwap-specific settings."""

    cosine_preprocessing = forms.BooleanField(
        required=False,
        initial=True,
        label=(
            "Use Preprocessing" if APP_LANG == "en" else "Effectuer un prétraitement"
        ),
        help_text=(
            "Filter less similar images before running algorithm"
            if APP_LANG == "en"
            else "Filtrer les images moins similaires avant d'exécuter l'algorithme"
        ),
        widget=forms.CheckboxInput(attrs={"class": "use-preprocessing"}),
    )
    cosine_n_filter = forms.IntegerField(
        min_value=2,
        initial=10,
        label=(
            "Number of images to keep"
            if APP_LANG == "en"
            else "Nombre d'images à conserver"
        ),
        widget=forms.NumberInput(attrs={"extra-class": "preprocessing-field"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.order_fields(
            ["cosine_preprocessing"]
            + list(BaseFeatureExtractionForm.Meta.fields)
            + ["cosine_n_filter"]
        )


class CosineSimilarityForm(SubForm, BaseFeatureExtractionForm):
    """Form for cosine similarity-specific settings."""

    # # NOTE NOT USED for now
    # top_k = forms.IntegerField(
    #     min_value=1,
    #     max_value=100,
    #     initial=10,
    #     label="Number of similar images to keep",
    #     widget=forms.NumberInput(attrs={"extra-class": "preprocessing-field"}),
    # )

    # NOTE for watermarks only
    # use_transpositions = forms.BooleanField(
    #     required=False,
    #     initial=False,
    #     label="Use Transpositions",
    #     help_text="Include transposed images in similarity computation",
    #     widget=forms.CheckboxInput(attrs={"extra-class": "preprocessing-field"}),
    # )


class SegSwapForm(SubForm, CosinePreprocessing):
    """Form for SegSwap-specific settings."""


class SimilarityAlgorithm(Enum):
    cosine = FormConfig(
        display_name="Cosine Similarity",
        description="Similarity using cosine distance between feature vectors",
        form_class=CosineSimilarityForm,
    )
    segswap = FormConfig(
        display_name="SegSwap",
        description="Similarity using correspondence matching between part of images",
        form_class=SegSwapForm,
    )

    @property
    def config(self):
        return self.value

    @classmethod
    def choices(cls):
        return [(algo.name, algo.config.display_name) for algo in cls]
