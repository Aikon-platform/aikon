from .base import *

API_URL = ENV.str(
    "API_URL", default=f"http://localhost:{ENV.int('API_PORT', default=5001)}"
)
BASE_URL = ENV.str("BASE_URL", default=f"http://localhost:{APP_PORT}")
APP_URL = BASE_URL
CANTALOUPE_APP_URL = ENV.str(
    "CANTALOUPE_BASE_URI", default=f"http://localhost:{CANTALOUPE_PORT}"
)
AIIINOTATE_BASE_URL = ENV.str("AIIINOTATE_BASE_URL")
MIRADOR_BASE_URL = ENV.str("MIRADOR_BASE_URL")

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
