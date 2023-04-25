from django import forms
from vhsapp.models.models import Place
from dal import autocomplete


class PlaceForm(forms.ModelForm):
    class Meta:
        model = Place
        fields = "__all__"
        widgets = {"name": autocomplete.ListSelect2(url="place-autocomplete")}
