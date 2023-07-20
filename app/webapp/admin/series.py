import nested_admin
from admin_extra_buttons.mixins import ExtraButtonsMixin
from django.contrib import admin

from app.webapp.admin import RoleInline
from app.webapp.admin.witness import WitnessInline
from app.webapp.models.series import Series, get_name


@admin.register(Series)
class SeriesAdmin(nested_admin.NestedModelAdmin):
    search_fields = ("edition_name",)

    class Meta:
        verbose_name = get_name("Series")
        verbose_name_plural = get_name("Series", True)

    class Media:
        css = {"all": ("css/form.css",)}
        js = ("js/witness-form.js",)

    fields = ["edition", ("date_min", "date_max"), "notes", "is_public"]

    inlines = [RoleInline, WitnessInline]

    # NOTE: attribute to use to change to template of witness (template at: templates/admin/series_form.html)
    # change_form_template = "admin/series_form.html"
