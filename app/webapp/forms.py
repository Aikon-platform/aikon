from django import forms
import ast

from app.webapp.models.place import Place
from dal import autocomplete

from app.webapp.models.utils.constants import LANGUAGES
from app.webapp.models.work import get_name


class PlaceForm(forms.ModelForm):
    class Meta:
        model = Place
        fields = "__all__"
        widgets = {
            "name": autocomplete.ListSelect2(
                url="place-autocomplete",
                attrs={
                    "data-placeholder": "Start typing to search...",
                },
                forward=["name"],
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
    lang = forms.MultipleChoiceField(
        choices=LANGUAGES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=get_name("languages"),
    )

    def __init__(self, *args, **kwargs):
        super(LanguageForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.lang:
            self.initial["lang"] = ast.literal_eval(self.instance.lang)
