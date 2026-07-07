from .base import *

PROD_URL = ENV.str("PROD_URL", default="")
BASE_URL = ENV.str("BASE_URL", default=f"https://{PROD_URL}")

API_URL = ENV.str("API_URL")
APP_URL = BASE_URL
APP_URL_FROM_DOCKER = ENV.str("APP_URL_FROM_DOCKER", default=APP_URL)
APP_URL_FROM_API = ENV.str("APP_URL_FROM_API", default=APP_URL)
CANTALOUPE_APP_URL = BASE_URL
AIIINOTATE_BASE_URL = ENV.str("AIIINOTATE_BASE_URL", default=f"{BASE_URL}/aiiinotate")
MIRADOR_BASE_URL = ENV.str("MIRADOR_BASE_URL", default=f"{BASE_URL}/mirador")

if ENV.str("HTTPS_PROXY", default=""):
    PROXIES = {
        "http": ENV.str("HTTP_PROXY", default=""),
        "https": ENV.str("HTTPS_PROXY", default=""),
        "no_proxy": ENV.str("NO_PROXY", default="localhost,127.0.0.1"),
    }

ADMIN_EMAIL = CONTACT_MAIL
ADMINS = [(f"{APP_NAME} admin", ADMIN_EMAIL)]

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_USE_TLS = ENV.bool("EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL = ENV.bool("EMAIL_USE_SSL", default=False)
EMAIL_HOST = ENV("EMAIL_HOST", default="localhost")
EMAIL_PORT = ENV.int("EMAIL_PORT", default=25)
EMAIL_HOST_USER = ENV("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = ENV("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = ENV("DEFAULT_FROM_EMAIL", default=f"noreply@{PROD_URL}")
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
            "django.security.DisallowedHost": {
                "handlers": ["mail_admins"],
                "level": "CRITICAL",
                "propagate": False,
            },
        },
    }
)
