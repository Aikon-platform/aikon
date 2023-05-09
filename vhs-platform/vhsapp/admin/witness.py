from django.contrib import admin

from vhsapp.models.conservation_place import Witness, get_name


@admin.register(Witness)
class WitnessAdmin(admin.ModelAdmin):
    search_fields = ("id_nb", "place")
    list_filter = ("id_nb", "place")

    fieldsets = (
        (None, {"fields": ("type", "id_nb")}),
        (
            "Optional Fields",
            {
                "fields": ("title",),
                "classes": ("collapse",),
                "description": 'Only display if type is "manuscript"',
            },
        ),
    )

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj=obj)
        if obj and obj.type != "manuscript":
            fieldsets = fieldsets[:-1]
        return fieldsets
