from django.contrib import admin
from admin_searchable_dropdown.filters import AutocompleteFilter

from vhsapp.models.admin import UnregisteredAdmin
from vhsapp.models.person import Person, get_name


class PersonFilter(AutocompleteFilter):
    title = get_name("name")
    field_name = "person"  # Name of the foreign key field in the Role model


@admin.register(Person)
class PersonAdmin(UnregisteredAdmin):
    search_fields = ("name",)
    # TODO
