from urllib.parse import urlparse

from .base import *

API_URL = f"http://{API_URL}" if not API_URL.startswith("http") else API_URL
BASE_URL = f"https://{ENV.str('PROD_URL', default='')}"

APP_URL = BASE_URL
CANTALOUPE_APP_URL = BASE_URL
SAS_APP_URL = f"{BASE_URL}/sas"

ADMIN_EMAIL = CONTACT_MAIL
EMAIL_HOST_USER = ENV("EMAIL_HOST_USER", default=ADMIN_EMAIL)
ADMINS = [(f"{APP_NAME} admin", ADMIN_EMAIL)]

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_USE_TLS = True
EMAIL_HOST = ENV("EMAIL_HOST", default="localhost")
EMAIL_PORT = ENV("EMAIL_PORT", default=587)
EMAIL_HOST_PASSWORD = ENV("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = ENV("DEFAULT_FROM_EMAIL", default=f"noreply@{APP_NAME}.com")
SERVER_EMAIL = ENV("SERVER_EMAIL", default=EMAIL_HOST_USER)

# Send automatic emails to the site admins when
LOGGING.update(
    {
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
