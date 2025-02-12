from django.contrib import admin
from admin_searchable_dropdown.filters import AutocompleteFilter

from app.webapp.admin.admin import UnregisteredAdmin
from app.webapp.models.place import Place, get_name
from app.webapp.forms import PlaceForm


class PlaceFilter(AutocompleteFilter):
    title = get_name("name")
    field_name = (
        "place"  # Name of the foreign key in the models that have a place fields
    )


@admin.register(Place)
class PlaceAdmin(UnregisteredAdmin):
    class Media:
        css = {"all": ("css/witness-form.css",)}

    change_form_template = "admin/form.html"
    form = PlaceForm
    search_fields = ("name", "country")
    list_filter = ("name",)
    list_per_page = 5

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index
        """
        return {}

    # # # # # # # # # # # #
    #     PERMISSIONS     #
    # # # # # # # # # # # #

    def has_change_permission(self, request, obj=None):
        return True

    def has_view_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request, obj=None):
        return True
