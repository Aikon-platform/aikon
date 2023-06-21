from django.contrib import admin

from app.webapp.admin.admin import UnregisteredAdmin
from app.webapp.models.content import Content, get_name


@admin.register(Content)
class ContentAdmin(UnregisteredAdmin):
    search_fields = ("work", "witness")
    # TODO
