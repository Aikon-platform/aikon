from django.contrib import admin
from admin_searchable_dropdown.filters import AutocompleteFilter

from app.webapp.admin.admin import UnregisteredAdmin
from app.webapp.models.place import Place, get_name


class PlaceFilter(AutocompleteFilter):
    title = get_name("name")
    field_name = (
        "place"  # Name of the foreign key in the models that have a place fields
    )


@admin.register(Place)
class PlaceAdmin(UnregisteredAdmin):
    search_fields = ("name",)
    # TODO
