from django.contrib import admin
from admin_searchable_dropdown.filters import AutocompleteFilter

from app.webapp.admin.admin import UnregisteredAdmin
from app.webapp.models.edition import Edition, get_name


class EditionFilter(AutocompleteFilter):
    title = get_name("Edition")
    field_name = "edition"  # name of field in Series


@admin.register(Edition)
class EditionAdmin(UnregisteredAdmin):
    change_form_template = "admin/form.html"
    search_fields = ("publisher__name", "place__name")
    autocomplete_fields = ("publisher", "place")
