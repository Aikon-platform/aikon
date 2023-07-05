from django.contrib import admin

from app.webapp.admin.admin import UnregisteredAdmin
from app.webapp.models.role import Role, get_name


@admin.register(Role)
class RoleAdmin(UnregisteredAdmin):
    # TODO might be unecessary to create a normal form if only the inline one is used
    search_fields = ("person_name", "role")


class RoleInline(admin.StackedInline):
    model = Role
    # TODO create the sub-form for Roles inside the Content sub-form
    autocomplete_fields = ("person",)
