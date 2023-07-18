from nested_admin import NestedStackedInline
from app.webapp.models.role import Role


class RoleInline(NestedStackedInline):
    model = Role
    extra = 1
    autocomplete_fields = ("person",)

    fields = [("role", "person")]
