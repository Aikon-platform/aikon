from urllib.parse import urlparse

from .base import *

prod_api_url = ENV.str("PROD_API_URL")
API_URL = (
    f"http://{prod_api_url}" if not prod_api_url.startswith("http") else prod_api_url
)
BASE_URL = f"https://{ENV.str('PROD_URL', default='')}"
APP_URL = BASE_URL
# CANTALOUPE_APP_URL = f"http://cantaloupe:{CANTALOUPE_PORT}" if DOCKER else BASE_URL
# SAS_APP_URL = f"http://sas:{SAS_PORT}" if DOCKER else f"{BASE_URL}/sas"
# NOTE Always use external URLs because SAS and Cantaloupe are used client side too
CANTALOUPE_APP_URL = BASE_URL
SAS_APP_URL = f"{BASE_URL}/sas"

if ENV.str("HTTPS_PROXY", default=""):
    PROXIES = {
        "http": ENV.str("HTTP_PROXY", default=""),
        "https": ENV.str("HTTPS_PROXY", default=""),
        "no_proxy": ENV.str("NO_PROXY", default="localhost,127.0.0.1"),
    }

ADMIN_EMAIL = CONTACT_MAIL
ADMINS = [(f"{APP_NAME} admin", ADMIN_EMAIL)]

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_USE_TLS = True
EMAIL_HOST = ENV("EMAIL_HOST", default="localhost")
EMAIL_PORT = ENV("EMAIL_PORT", default=587)
EMAIL_HOST_USER = ENV("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = ENV("EMAIL_HOST_PASSWORD", default="")

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
