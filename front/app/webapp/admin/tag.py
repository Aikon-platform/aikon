from django.contrib import admin
from admin_searchable_dropdown.filters import AutocompleteFilter

from app.webapp.models.tag import Tag, get_name


class TagFilter(AutocompleteFilter):
    title = get_name("Tag")
    field_name = "tags"  # name of field in Content


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    class Media:
        css = {"all": ("css/witness-form.css",)}

    change_form_template = "admin/form.html"
    search_fields = ("label",)
    list_filter = ("label",)
    list_display = ("id", "label")
    list_display_links = ("label",)
    ordering = ("id",)
