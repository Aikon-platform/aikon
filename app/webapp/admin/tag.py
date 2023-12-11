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

    search_fields = ("label",)
    list_filter = ("label",)
    list_display = ("id", "label")
    list_display_links = ("label",)
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
