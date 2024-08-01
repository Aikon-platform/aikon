from django.contrib import admin
from admin_searchable_dropdown.filters import AutocompleteFilter

from app.webapp.models.language import get_name, Language


class LanguageFilter(AutocompleteFilter):
    title = get_name("Language")
    field_name = get_name("lang")  # name of field in Content model


# NOTE: no form because all languages are added with populate_language migration
@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    class Media:
        css = {"all": ("css/witness-form.css",)}

    change_form_template = "admin/form.html"
    search_fields = ("lang",)
    list_filter = ("lang",)
    list_display = ("id", "lang")
    list_display_links = ("lang",)
    ordering = ("id",)
