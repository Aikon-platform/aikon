from django.contrib import admin
from admin_searchable_dropdown.filters import AutocompleteFilter

from app.webapp.admin.admin import UnregisteredAdmin
from app.webapp.models.person import Person, get_name


class PersonFilter(AutocompleteFilter):
    title = get_name("name")
    field_name = "person"  # Name of the foreign key field in the Role model
    ordering = ("name",)


@admin.register(Person)
class PersonAdmin(UnregisteredAdmin):
    change_form_template = "admin/form.html"
    search_fields = ("name",)
    list_filter = ("name",)
    list_per_page = 5

    fields = ["name", ("date_min", "date_max")]
