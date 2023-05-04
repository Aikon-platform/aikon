from django.contrib import admin
from admin_searchable_dropdown.filters import AutocompleteFilter

from vhsapp.models.admin import UnregisteredAdmin
from vhsapp.models.edition import Edition, get_name


class EditionFilter(AutocompleteFilter):
    title = get_name("Edition")
    field_name = "edition"  # name of field in Series


@admin.register(Edition)
class EditionAdmin(UnregisteredAdmin):
    search_fields = ("publisher_name", "place_name")
    # TODO
