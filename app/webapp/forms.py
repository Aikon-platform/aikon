from django import forms

from app.webapp.models.language import Language
from app.webapp.models.place import Place
from dal import autocomplete


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
    class Meta:
        model = Language
        fields = "__all__"
        widgets = {
            "lang": autocomplete.ModelSelect2Multiple(
                url="language-autocomplete",
                attrs={
                    "data-placeholder": "Start typing to search...",
                },
            ),
        }

    def __init__(self, *args, **kwargs):
        super(LanguageForm, self).__init__(*args, **kwargs)
        self.fields["lang"].help_text = None  # Set help_text to None to remove it
