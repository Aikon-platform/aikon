from django.contrib import admin
from admin_searchable_dropdown.filters import AutocompleteFilter

from vhsapp.models.admin import UnregisteredAdmin
from vhsapp.models.conservation_place import ConservationPlace, get_name


class ConservationPlaceFilter(AutocompleteFilter):
    title = get_name("ConservationPlace")
    field_name = "place"  # name of field in Witness


@admin.register(ConservationPlace)
class ConservationPlaceAdmin(UnregisteredAdmin):
    search_fields = ("name",)
    list_filter = ("name",)
