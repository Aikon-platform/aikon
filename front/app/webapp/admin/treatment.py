from django.contrib import admin

from app.webapp.admin import UnregisteredAdmin
from app.webapp.models.treatment import Treatment


@admin.register(Treatment)
class TreatmentAdmin(UnregisteredAdmin):
    search_fields = (
        "task_type",
        "set_id",
    )
    list_filter = ("task_type",)

    change_form_template = "admin/form.html"
    list_per_page = 100
