from urllib.parse import urlparse

from .base import *

ADMINS = [(f"{APP_NAME} admin", ADMIN_EMAIL)]

API_URL = ENV("API_URL")

APP_URL = f"{PROD_URL}"
CANTALOUPE_APP_URL = f"{PROD_URL}"
SAS_APP_URL = f"{PROD_URL}/sas"

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_USE_TLS = True

EMAIL_HOST = ENV("EMAIL_HOST", default="localhost")
EMAIL_PORT = ENV("EMAIL_PORT", default=587)
EMAIL_HOST_PASSWORD = ENV("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = ENV("DEFAULT_FROM_EMAIL", default=f"noreply@{APP_NAME}.com")
SERVER_EMAIL = ENV("SERVER_EMAIL", default=EMAIL_HOST_USER)

LOGGING.update(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "mail_admins": {
                "level": "ERROR",
                "class": "django.utils.log.AdminEmailHandler",
                "include_html": True,
            },
        },
        "loggers": {
            "django.request": {
                "handlers": ["mail_admins"],
                "level": "ERROR",
                "propagate": True,
            },
        },
    }
)
