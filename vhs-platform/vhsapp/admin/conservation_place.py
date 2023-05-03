from django.contrib import admin

from vhsapp.models.conservation_place import (
    ConservationPlace,
)


@admin.register(ConservationPlace)
class ConservationPlaceAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_filter = ("name",)
    list_per_page = 5

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index
        """
        return {}
