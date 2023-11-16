from django.contrib import admin
from admin_searchable_dropdown.filters import AutocompleteFilter

from app.webapp.admin.admin import UnregisteredAdmin
from app.webapp.models.volume import Volume, get_name


class VolumeFilter(AutocompleteFilter):
    title = get_name("Volume")
    field_name = "volume"  # name of field in Witness


@admin.register(Volume)
class VolumeAdmin(UnregisteredAdmin):
    search_fields = ("number",)
    list_filter = ("number",)
    # fields = [("title", "number")]
    autocomplete_fields = ("edition",)
