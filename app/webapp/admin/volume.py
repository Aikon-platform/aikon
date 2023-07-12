from django.contrib import admin
from admin_searchable_dropdown.filters import AutocompleteFilter

from app.webapp.admin.admin import UnregisteredAdmin
from app.webapp.models.volume import Volume, get_name


class VolumeFilter(AutocompleteFilter):
    title = get_name("Volume")
    field_name = "volume"  # name of field in Witness


@admin.register(Volume)
class VolumeAdmin(UnregisteredAdmin):
    search_fields = ("title",)
    list_filter = ("title",)
    autocomplete_fields = ("edition",)


class VolumeInline(admin.StackedInline):
    # NOTE Inline and not just only autocomplete_field? there won't be many version of one volume in the platform

    model = Volume
    # TODO create the sub-form for Volume inside the Content sub-form
    autocomplete_fields = ("edition",)
