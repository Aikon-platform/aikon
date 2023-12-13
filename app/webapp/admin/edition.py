from django.contrib import admin
from admin_searchable_dropdown.filters import AutocompleteFilter

from app.webapp.admin.admin import UnregisteredAdmin
from app.webapp.models.edition import Edition, get_name


class EditionFilter(AutocompleteFilter):
    title = get_name("Edition")
    field_name = "edition"  # name of field in Series


@admin.register(Edition)
class EditionAdmin(UnregisteredAdmin):
    search_fields = ("publisher__name", "place_name")
    autocomplete_fields = ("publisher", "place")
    # TODO create list of fields that are displayed in list view
