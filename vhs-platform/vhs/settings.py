import environ
from vhsapp.utils.paths import BASE_DIR, LOG_PATH, MEDIA_PATH, STATIC_PATH
from vhsapp.utils.constants import APP_NAME

# Build paths inside the project like this: BASE_DIR / 'subdir'.

ENV = environ.Env()
environ.Env.read_env(env_file=f"{BASE_DIR}/vhs/.env")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ENV("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = ENV.bool("DEBUG")

ALLOWED_HOSTS = ENV.list("ALLOWED_HOSTS")

APP_LANG = ENV("APP_LANG")


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "vhsapp",
    "nested_admin",
    "fontawesomefree",
    "admin_searchable_dropdown",
    "corsheaders",
    "admin_extra_buttons",
]

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
# VHS, CANTALOUPE, SAS
VHS_PORT = 8000
CANTALOUPE_PORT = 8182
SAS_PORT = 8888

VHS_APP_URL = f"http://localhost:{VHS_PORT}"
CANTALOUPE_APP_URL = f"http://localhost:{CANTALOUPE_PORT}"
SAS_APP_URL = f"http://localhost:{SAS_PORT}"

# Override the default values in production mode
if not DEBUG:
    VHS_APP_URL = "https://eida.obspm.fr"
    CANTALOUPE_APP_URL = "https://eida.obspm.fr"
    SAS_APP_URL = "https://eida.obspm.fr/sas"

ROOT_URLCONF = "vhs.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "vhsapp.context_processors.global_variables",
            ],
            "builtins": [
                "vhsapp.filters",
            ],
        },
    },
]

WSGI_APPLICATION = "vhs.wsgi.application"

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

LANGUAGE_CODE = "fr-FR"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / STATIC_PATH

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / MEDIA_PATH

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
        APP_NAME: {
            "handlers": ["file"],
            "level": "ERROR",
        },
    },
    "formatters": {
        "verbose": {"format": "%(asctime)s - %(levelname)s - %(message)s"},
    },
}

# Celery settings
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
