import nested_admin
from admin_extra_buttons.mixins import ExtraButtonsMixin
from django.contrib import admin

from app.webapp.admin import DigitizationInline
from app.webapp.models import VOL
from app.webapp.models.series import Series, get_name


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    search_fields = ("edition_name",)

    # class WitnessAdmin(ExtraButtonsMixin, admin.ModelAdmin):
    class Meta:
        verbose_name = get_name("Series")
        verbose_name_plural = get_name("Series", True)
        abstract = True

    class Media:
        css = {"all": ("css/style.css",)}
        js = ("js/jquery-3.6.1.js", "js/script.js")

    # NOTE: attribute to use to change to template of witness (template at: templates/admin/change.html)
    # change_form_template = "admin/change.html"
