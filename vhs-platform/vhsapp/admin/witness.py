from django.contrib import admin

from vhsapp.models.conservation_place import Witness, get_name


@admin.register(Witness)
class WitnessAdmin(admin.ModelAdmin):
    search_fields = ("id_nb", "place")
    list_filter = ("id_nb", "place")
    # info on fieldsets: https://docs.djangoproject.com/en/4.2/ref/contrib/admin/#django.contrib.admin.ModelAdmin.fieldsets
    fieldsets = (
        (
            None,
            {"fields": ["type", ("id_nb", "place")]},
        ),  # place and id_nb should appear on the same line
        (
            "Optional Fields",
            {
                "fields": ("title",),
                "classes": ("collapse",),  # probably not collapse
                "description": 'Only display if type is "manuscript"',
            },
        ),
    )

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj=obj)
        if obj and obj.type != "manuscript":
            fieldsets = fieldsets[:-1]
        return fieldsets
