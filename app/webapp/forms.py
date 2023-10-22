from django import forms

from app.config.settings import GEONAMES_USER
from app.webapp.models.place import Place
from dal import autocomplete

from app.webapp.utils.constants import MAX_ROWS
from app.webapp.utils.functions import get_json


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
