from django.contrib import admin

from app.webapp.admin.admin import UnregisteredAdmin
from app.webapp.models.role import Role, get_name


@admin.register(Role)
class RoleAdmin(UnregisteredAdmin):
    search_fields = ("person_name", "role")
