import environ
from app.webapp.utils.paths import BASE_DIR, MEDIA_DIR, STATIC_DIR

ENV = environ.Env()
environ.Env.read_env(env_file=f"{BASE_DIR}/config/.env")

APP_NAME = ENV.str("APP_NAME", default="")
WEBAPP_NAME = "webapp"
ADDITIONAL_MODULES = ENV.list("INSTALLED_APPS", default=[])

# Logos to be displayed in the footer
APP_LOGO = ENV.list("APP_LOGO", default=[])

LOGIN_URL = f"/{APP_NAME}-admin/login/"
LOGIN_REDIRECT_URL = "/"

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ENV.str("SECRET_KEY", default="")

TARGET = ENV("TARGET", default="dev")
DOCKER = ENV.bool("DOCKER", default=False)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = ENV.bool("DEBUG", default=False if TARGET == "prod" else True)

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
    "django_filters",
    "crispy_forms",
    f"{WEBAPP_NAME}",
] + ADDITIONAL_MODULES

hosts = ENV.list("ALLOWED_HOSTS", default=[]) + [ENV.str("PROD_URL", default="")]
hosts += ["web"]  # for docker nginx service
https_hosts = [f"https://{host}" for host in hosts]
wildcard_hosts = [f"https://*.{host}" for host in hosts if "." in host]

ALLOWED_HOSTS = hosts + https_hosts + wildcard_hosts
CSRF_TRUSTED_ORIGINS = https_hosts + wildcard_hosts

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

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

DATA_UPLOAD_MAX_MEMORY_SIZE = 500 * 1024 * 1024  # 500MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 500 * 1024 * 1024  # 500MB

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
        # "file": {
        #     "class": "logging.FileHandler",
        #     "filename": LOG_PATH,
        #     "level": "ERROR",
        #     "formatter": "verbose",
        # },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "celery": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
    "formatters": {
        "verbose": {"format": "%(asctime)s - %(levelname)s - %(message)s"},
    },
}

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

# Define the default values for application URLs in development mode
# APP, CANTALOUPE, SAS
APP_PORT = ENV.int("FRONT_PORT", 8000)
CANTALOUPE_PORT = ENV.int("CANTALOUPE_PORT", 8182)

GEONAMES_USER = ENV.str("GEONAMES_USER", default="")

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
                "webapp.templatetags.context_processors.global_variables",
                "webapp.context_processors.login_url",
            ],
            "builtins": [
                "webapp.templatetags.filters",
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
        "NAME": ENV.str("POSTGRES_DB", default=""),
        "USER": ENV.str("POSTGRES_USER", default=""),
        "PASSWORD": ENV.str("POSTGRES_PASSWORD", default=""),
        "HOST": "db" if DOCKER else "localhost",
        "PORT": ENV.str("DB_PORT", default=5432),
    },
    "test": {"NAME": f"test_{ENV.str('POSTGRES_DB', default='')}"},
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

APP_LANG = ENV.str("APP_LANG", default="en")
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

CRISPY_TEMPLATE_PACK = "bootstrap4"

EMAIL_HOST_USER = ENV("EMAIL_HOST_USER")
CONTACT_MAIL = ENV("CONTACT_EMAIL", default=EMAIL_HOST_USER)
