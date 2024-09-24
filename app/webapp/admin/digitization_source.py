from django.contrib import admin
from app.webapp.admin.admin import UnregisteredAdmin
from app.webapp.models.digitization_source import DigitizationSource


@admin.register(DigitizationSource)
class DigitizationSourceAdmin(UnregisteredAdmin):
    change_form_template = "admin/form.html"
    search_fields = ("source",)
