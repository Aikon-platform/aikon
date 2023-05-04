from django.contrib import admin
from admin_searchable_dropdown.filters import AutocompleteFilter

from vhsapp.models.admin import UnregisteredAdmin
from vhsapp.models.tag import Tag, get_name


class TagFilter(AutocompleteFilter):
    title = get_name("Tag")
    field_name = "tags"  # name of field in Content


@admin.register(Tag)
class TagAdmin(UnregisteredAdmin):
    search_fields = ("label",)
    list_filter = ("label",)
