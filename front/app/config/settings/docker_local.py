# NOTE in a docker/nginx config,
#   - the only entrypoint of the app must be the NGINX host:
#       it will redirect queries to other containers.
#   - other containers are reached NOT by localhost:$PORT,
#       but by localhost:$NGINX_PORT/$CONTAINER_NAME.
#       in our .env templates, when using docker we define all *_HOST
#       variables by their container name.

from .base import *

# TODO allow docker_local to run in DEBUG as well
# avoid livereload uninstalled error.
DEBUG = False

nginx_port = ENV("NGINX_PORT", default=8182)
if not nginx_port:
    raise ValueError(
        f"env variable NGINX_PORT is not defined ! Docker local config impossible !"
    )

API_URL = f'http://localhost:{ENV("API_PORT", default=5000)}'
BASE_URL = f"http://localhost:{nginx_port}"

# nginx redirects "/" queries to docker.
APP_URL = f"{BASE_URL}"

# cantaloupe urls are targeted by `BASE_URL/iiif/`, which is done at route level and not here.
CANTALOUPE_APP_URL = f"{BASE_URL}"

# override AIIINOTATE and MIRADOR variables by their nginx counterparts
AIIINOTATE_HOST = f"{BASE_URL}/{ENV('AIIINOTATE_HOST', default='aiiinotate')}"
AIIINOTATE_BASE_URL = AIIINOTATE_HOST
MIRADOR_HOST = f"{BASE_URL}/{ENV('MIRADOR_HOST', default='mirador')}"
MIRADOR_BASE_URL = MIRADOR_HOST

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# disable CSRF token validation and add localhost to the trusted hosts.
USE_X_FORWARDED_HOST = True
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "web"]
CSRF_TRUSTED_ORIGINS = [f"http://localhost:{nginx_port}"]

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
