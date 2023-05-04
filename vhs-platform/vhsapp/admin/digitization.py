from django.contrib import admin

from vhsapp.models.admin import UnregisteredAdmin
from vhsapp.models.digitization import Digitization, get_name


@admin.register(Digitization)
class DigitizationAdmin(UnregisteredAdmin):
    search_fields = ("witness",)
    # TODO
