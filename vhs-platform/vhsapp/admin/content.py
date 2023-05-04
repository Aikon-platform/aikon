from django.contrib import admin

from vhsapp.models.admin import UnregisteredAdmin
from vhsapp.models.content import Content, get_name


@admin.register(Content)
class ContentAdmin(UnregisteredAdmin):
    search_fields = ("work", "witness")
    # TODO
