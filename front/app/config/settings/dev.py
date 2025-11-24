from .base import *

DEBUG = True

API_URL = f'http://localhost:{ENV("API_PORT", default=5000)}'
BASE_URL = f"http://localhost:{ENV('FRONT_PORT', default=8000)}"

APP_URL = f"http://localhost:{APP_PORT}"
CANTALOUPE_APP_URL = f"http://localhost:{CANTALOUPE_PORT}"

# django-environ doesn't support variable expansion in the .env => recreate AIIINOTATE_BASE_URL and MIRADOR_BASE_URL manually
AIIINOTATE_HOST = ENV("AIIINOTATE_HOST")
AIIINOTATE_SCHEME = ENV("AIIINOTATE_SCHEME")
AIIINOTATE_PORT = ENV("AIIINOTATE_PORT")
AIIINOTATE_BASE_URL = f"{AIIINOTATE_SCHEME}://{AIIINOTATE_HOST}:{AIIINOTATE_PORT}"
MIRADOR_HOST = ENV("MIRADOR_HOST")
MIRADOR_SCHEME = ENV("MIRADOR_SCHEME")
MIRADOR_PORT = ENV("MIRADOR_PORT")
MIRADOR_SCHEME = ENV("MIRADOR_SCHEME")
MIRADOR_BASE_URL = f"{MIRADOR_SCHEME}://{MIRADOR_HOST}:{MIRADOR_PORT}"

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
