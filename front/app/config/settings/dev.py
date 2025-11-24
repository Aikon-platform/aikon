from .base import *

DEBUG = True

API_URL = f'http://localhost:{ENV("API_PORT", default=5000)}'
BASE_URL = f"http://localhost:{ENV('FRONT_PORT', default=8000)}"

APP_URL = f"http://localhost:{APP_PORT}"
CANTALOUPE_APP_URL = f"http://localhost:{CANTALOUPE_PORT}"
AIIINOTATE_BASE_URL = ENV("AIIINOTATE_BASE_URL")

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

LOGGING.update(
    {
        "loggers": {
            "django": {
                "handlers": ["console"],
                "level": "INFO",
            },
            "celery": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": True,
            },
        },
    }
)
