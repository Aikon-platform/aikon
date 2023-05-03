from django.contrib import admin

from vhsapp.models.conservation_place import Witness, get_name


@admin.register(Witness)
class WitnessAdmin(admin.ModelAdmin):
    search_fields = ("id_nb", "place")
    list_filter = ("id_nb", "place")
