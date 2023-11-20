from django.contrib import admin
from admin_searchable_dropdown.filters import AutocompleteFilter

from app.webapp.admin.admin import UnregisteredAdmin
from app.webapp.forms import LanguageForm
from app.webapp.models.work import Work, get_name


class WorkFilter(AutocompleteFilter):
    title = get_name("Work")
    field_name = "work"  # name of field in Content


@admin.register(Work)
class WorkAdmin(UnregisteredAdmin):
    form = LanguageForm
    search_fields = ("title",)
    list_filter = ("title",)
    fields = [
        "title",
        "author",
        ("date_min", "date_max"),
        "place",
        "notes",
        "lang",
        "tags",
    ]
    autocomplete_fields = ("author", "place")


# class WorkInline(nested_admin.NestedStackedInline):
#     fields = ["title", "author", ("date_min", "date_max")]
