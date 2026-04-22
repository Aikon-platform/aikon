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

nginx_port = ENV("NGINX_PORT", default=8080)
if not nginx_port:
    raise ValueError(
        f"env variable NGINX_PORT is not defined ! Docker local config impossible !"
    )

# NOTE: in localhost, it is impossible to connect to a remote API:
# the API needs to fetch data from the app, but the app is only exposed to localhost
# => API and front app must be on the same machine.
API_URL = f'http://localhost:{ENV("API_PORT", default=5000)}'

# NOTE:     IOHDNLAKJNF;KLajGB;KAEJBFL
BASE_URL_SERVER_SIDE = f"http://nginx:{nginx_port}"
BASE_URL_CLIENT_SIDE = f"http://localhost:{nginx_port}"

# nginx redirects "/" queries to the django docker.
APP_URL = f"{BASE_URL_CLIENT_SIDE}"

# cantaloupe urls are targeted by `BASE_URL/iiif/`, which is done at route level and not here.
CANTALOUPE_APP_URL = f"{BASE_URL_CLIENT_SIDE}"

# override AIIINOTATE_BASE_URL and MIRADOR_BASE_URL variables by their nginx counterparts
AIIINOTATE_BASE_URL = (
    f"{BASE_URL_SERVER_SIDE}/{ENV('AIIINOTATE_HOST', default='aiiinotate')}"
)
MIRADOR_BASE_URL = f"{BASE_URL_CLIENT_SIDE}/{ENV('MIRADOR_HOST', default='mirador')}"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# disable CSRF token validation and add localhost to the trusted hosts.
USE_X_FORWARDED_HOST = True
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "web", "nginx"]
CSRF_TRUSTED_ORIGINS = [BASE_URL_SERVER_SIDE, BASE_URL_CLIENT_SIDE]

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
