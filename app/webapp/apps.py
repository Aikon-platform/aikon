from django.apps import AppConfig

from app.webapp.utils.constants import APP_NAME_CAPITALIZED


class PlatformConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "webapp"
    # Name that will be displayed in the sidebar of the admin interface
    verbose_name = APP_NAME_CAPITALIZED
