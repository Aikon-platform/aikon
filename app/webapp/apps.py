from django.apps import AppConfig

from app.config.settings import APP_NAME


class PlatformConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "webapp"
    verbose_name = APP_NAME
