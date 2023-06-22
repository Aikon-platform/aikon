from django.contrib import admin

from app.webapp.admin import UnregisteredAdmin
from app.webapp.models.digitization import Digitization, get_name


@admin.register(Digitization)
class DigitizationAdmin(UnregisteredAdmin):
    search_fields = ("witness",)
