from django.contrib import admin
from admin_searchable_dropdown.filters import AutocompleteFilter

from app.webapp.admin.admin import UnregisteredAdmin
from app.webapp.models.conservation_place import ConservationPlace, get_name


class ConservationPlaceFilter(AutocompleteFilter):
    title = get_name("ConservationPlace")
    field_name = "place__name"
    ordering = ("place__city__name",)


@admin.register(ConservationPlace)
class ConservationPlaceAdmin(UnregisteredAdmin):
    search_fields = ("name", "city__name", "city__country")
    list_filter = ("name", "city__name")
