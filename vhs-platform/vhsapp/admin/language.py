from django.contrib import admin
from admin_searchable_dropdown.filters import AutocompleteFilter

from vhsapp.models.admin import UnregisteredAdmin
from vhsapp.models.Language import Language, get_name


class LanguageFilter(AutocompleteFilter):
    title = get_name("Language")
    field_name = "place"  # name of field in Witness
