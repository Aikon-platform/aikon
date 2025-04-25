from urllib.parse import urlparse

from .base import *

prod_api_url = ENV.str("PROD_API_URL")
API_URL = (
    f"http://{prod_api_url}" if not prod_api_url.startswith("http") else prod_api_url
)
PROD_URL = ENV.str("PROD_URL", default="")
BASE_URL = f"https://{PROD_URL}"
APP_URL = BASE_URL
# CANTALOUPE_APP_URL = f"http://cantaloupe:{CANTALOUPE_PORT}" if DOCKER else BASE_URL
# SAS_APP_URL = f"http://sas:{SAS_PORT}" if DOCKER else f"{BASE_URL}/sas"
CANTALOUPE_APP_URL = BASE_URL
SAS_APP_URL = f"{BASE_URL}/sas"

if ENV.str("HTTPS_PROXY", default=""):
    PROXIES = {
        "http": ENV.str("HTTP_PROXY", default=""),
        "https": ENV.str("HTTPS_PROXY", default=""),
        "no_proxy": ENV.str("NO_PROXY", default="localhost,127.0.0.1"),
    }

ADMIN_EMAIL = CONTACT_MAIL
EMAIL_HOST_USER = ENV("EMAIL_HOST_USER", default=ADMIN_EMAIL)
ADMINS = [(f"{APP_NAME} admin", ADMIN_EMAIL)]

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_USE_TLS = True
EMAIL_HOST = ENV("EMAIL_HOST", default="localhost")
EMAIL_PORT = ENV("EMAIL_PORT", default=587)
EMAIL_HOST_PASSWORD = ENV("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = ENV("DEFAULT_FROM_EMAIL", default=f"noreply@{PROD_URL}")
SERVER_EMAIL = ENV("SERVER_EMAIL", default=EMAIL_HOST_USER)

# if DOCKER:
#     EMAIL_USE_TLS = False
#     EMAIL_HOST = ENV("EMAIL_HOST", default="mailserver")
#     EMAIL_PORT = ENV("EMAIL_PORT", default=25)
#     EMAIL_HOST_PASSWORD = ENV("EMAIL_HOST_PASSWORD", default="")
#     DEFAULT_FROM_EMAIL = ENV("DEFAULT_FROM_EMAIL", default=f"noreply@{PROD_URL}")
#     SERVER_EMAIL = ENV("SERVER_EMAIL", default=EMAIL_HOST_USER)

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
