from django.contrib import admin, messages

from app.config.settings import APP_LANG
from app.webapp.admin import UnregisteredAdmin
from app.webapp.models.series import Series
from app.webapp.models.treatment import Treatment
from app.webapp.models.witness import Witness
from app.webapp.models.work import Work


@admin.register(Treatment)
class TreatmentAdmin(UnregisteredAdmin):
    search_fields = (
        "task_type",
        "set_id",
    )
    list_filter = ("task_type",)

    change_form_template = "admin/form.html"
    list_per_page = 100
