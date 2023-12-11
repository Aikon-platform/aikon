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

    search_fields = ("lang",)
    list_filter = ("lang",)
    list_display = ("id", "lang")
    list_display_links = ("lang",)
    ordering = ("id",)

    def has_module_permission(self, request):
        """
        Check if the user has permission to view the module
        In this case, return True only if the user is a superadmin
        """
        return request.user.is_superuser

    def has_add_permission(self, request):
        """
        Deny add permission if not a superadmin
        """
        return request.user.is_superuser
