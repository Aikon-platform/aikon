from django.contrib import admin

from vhsapp.models.admin import UnregisteredAdmin
from vhsapp.models.role import Role, get_name


@admin.register(Role)
class RoleAdmin(UnregisteredAdmin):
    search_fields = ("person_name", "role")
