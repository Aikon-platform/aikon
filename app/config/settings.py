import environ
from app.webapp.utils.paths import BASE_DIR, LOG_PATH, MEDIA_DIR, STATIC_DIR

ENV = environ.Env()
environ.Env.read_env(env_file=f"{BASE_DIR}/config/.env")

APP_NAME = ENV("APP_NAME")
WEBAPP_NAME = "webapp"

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ENV("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = ENV.bool("DEBUG")

# Enabled modules
ADDITIONAL_MODULES = [
    # "similarity",
]

INSTALLED_APPS = [
    "dal",
    "dal_select2",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "nested_admin",
    "fontawesomefree",
    "admin_searchable_dropdown",
    "corsheaders",
    "admin_extra_buttons",
    f"{WEBAPP_NAME}",
]
INSTALLED_APPS += ADDITIONAL_MODULES

hosts = ENV.list("ALLOWED_HOSTS")
hosts.append(ENV("PROD_URL"))
ALLOWED_HOSTS = hosts
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

APP_LANG = ENV("APP_LANG")

CONTACT_MAIL = ENV("CONTACT_MAIL")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "corsheaders.middleware.CorsMiddleware",
]

if DEBUG:
    INSTALLED_APPS += [
        "livereload",
        "debug_toolbar",
    ]
    MIDDLEWARE += [
        "livereload.middleware.LiveReloadScript",
        "debug_toolbar.middleware.DebugToolbarMiddleware",
    ]
    INTERNAL_IPS = [
        "127.0.0.1",
    ]
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "console": {"class": "logging.StreamHandler"},
        },
        "loggers": {
            "django": {
                "handlers": ["console"],
                "level": "INFO",
            },
        },
    }

# Define the default values for application URLs in development mode
# APP, CANTALOUPE, SAS
APP_PORT = 8000
CANTALOUPE_PORT = ENV("CANTALOUPE_PORT")
SAS_PORT = ENV("SAS_PORT")

APP_URL = f"http://localhost:{APP_PORT}"
CANTALOUPE_APP_URL = f"http://localhost:{CANTALOUPE_PORT}"
SAS_APP_URL = f"http://localhost:{SAS_PORT}"

EXAPI_URL = ENV("EXAPI_URL")
EXTRACTOR_MODEL = ENV("EXTRACTOR_MODEL")
GEONAMES_USER = ENV("GEONAMES_USER")

PROD_URL = f"https://{ENV('PROD_URL')}"

# Override the default values in production mode
if not DEBUG:
    APP_URL = f"{PROD_URL}"
    CANTALOUPE_APP_URL = f"{PROD_URL}"
    SAS_APP_URL = f"{PROD_URL}/sas"

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "webapp" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "webapp.context_processors.global_variables",
            ],
            "builtins": [
                "webapp.filters",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": ENV("DB_NAME"),
        "USER": ENV("DB_USERNAME"),
        "PASSWORD": ENV("DB_PASSWORD"),
        "HOST": ENV("DB_HOST"),
        "PORT": ENV("DB_PORT"),
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

APP_LANG = ENV("APP_LANG")
LANGUAGE_CODE = "en-us" if APP_LANG == "en" else "fr-FR"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / STATIC_DIR

MEDIA_URL = "media/"
MEDIA_ROOT = MEDIA_DIR

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Maximum number of form fields to read from a request
# The default value is 1000

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240

# Cross-Origin Resource Sharing (CORS) from any origin
CORS_ALLOW_ALL_ORIGINS = True

# Configure logging to record ERROR level messages to file
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "filename": LOG_PATH,
            "level": "ERROR",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "level": "WARNING",
        },
    },
    "formatters": {
        "verbose": {"format": "%(asctime)s - %(levelname)s - %(message)s"},
    },
}

# # Celery settings
# CELERY_BROKER_URL = f"redis://:{ENV('REDIS_PASSWORD')}@localhost:6379/0"
# CELERY_RESULT_BACKEND = f"redis://:{ENV('REDIS_PASSWORD')}@localhost:6379/0"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = ENV("EMAIL_HOST")
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = ENV("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = ENV("EMAIL_HOST_PASSWORD")
