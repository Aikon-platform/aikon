from django.contrib import admin

from vhsapp.models.conservation_place import Series, get_name


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    search_fields = ("edition_name",)
