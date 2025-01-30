from django import forms

from app.config.settings import APP_LANG
from app.webapp.models.language import Language
from app.webapp.models.place import Place
from dal import autocomplete

from app.webapp.models.user_profile import UserProfile

SEARCH_MSG = "Search..." if APP_LANG == "en" else "Rechercher..."


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


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            "picture",
            "role",
            "affiliation",
            "presentation",
            "is_team",
        ]
