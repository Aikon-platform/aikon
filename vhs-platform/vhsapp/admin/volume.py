from django.contrib import admin
from admin_searchable_dropdown.filters import AutocompleteFilter

from vhsapp.models.admin import UnregisteredAdmin
from vhsapp.models.volume import Volume, get_name


class VolumeFilter(AutocompleteFilter):
    title = get_name("Volume")
    field_name = "volume"  # name of field in Witness


@admin.register(Volume)
class VolumeAdmin(UnregisteredAdmin):
    search_fields = ("name",)
    list_filter = ("name",)
