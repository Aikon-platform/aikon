from .base import *

DEBUG = True

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

API_URL = f'http://localhost:{ENV("API_DEV_PORT", default=5000)}'
BASE_URL = f"http://localhost:{ENV('FRONT_DEV_PORT', default=8000)}"
# LOGIN_REQUIRED = False
LOGIN_REQUIRED = True
