from django.contrib import admin
from nested_admin import NestedStackedInline

from app.webapp.admin.admin import UnregisteredAdmin
from app.webapp.models.role import Role, get_name


@admin.register(Role)
class RoleAdmin(UnregisteredAdmin):
    # TODO might be unnecessary to create a normal form if only the inline one is used
    search_fields = ("person_name", "role")


class RoleInline(NestedStackedInline):
    model = Role
    extra = 1
    autocomplete_fields = ("person",)
