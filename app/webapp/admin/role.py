from nested_admin import NestedStackedInline
from app.webapp.models.role import Role


class RoleInline(NestedStackedInline):
    model = Role
    template = "admin/includes/inline_fieldset.html"
    verbose_name_plural = None  # No title in the blue banner on top of the inline form
    extra = 1

    fields = [("role", "person")]
    # autocomplete_fields = ("person",)
