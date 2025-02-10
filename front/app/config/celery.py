import os
import sys
import environ
from celery import Celery

from app.webapp.utils.paths import BASE_DIR

# Django application configuration
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ENV = environ.Env()
environ.Env.read_env(env_file=f"{BASE_DIR}/config/.env")
DEBUG = ENV.bool("DEBUG", default=True)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.config.settings")

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = os.environ.get("REDIS_PORT", "6379")
REDIS_PASSWORD = ENV.str("REDIS_PASSWORD", default="")

redis_prefix = f"redis://:{REDIS_PASSWORD}@" if REDIS_PASSWORD else "redis://"

ADDITIONAL_MODULES = ENV.list("ADDITIONAL_MODULES", default=[])

imported_tasks = ("app.webapp.tasks",)
for module in ADDITIONAL_MODULES:
    imported_tasks += (f"app.{module}.tasks",)

celery_app = Celery(
    "config",
    broker=f"{redis_prefix}{REDIS_HOST}:{REDIS_PORT}/0",
    backend=f"{redis_prefix}{REDIS_HOST}:{REDIS_PORT}/0",
    imports=imported_tasks,
)

# Load Celery configuration from Django settings
celery_app.config_from_object("django.conf:settings", namespace="CELERY")
celery_app.conf.broker_connection_retry_on_startup = True

celery_app.conf.update(
    CELERY_ACCEPT_CONTENT=["json", "pickle"],
    CELERY_TASK_SERIALIZER="pickle",
    CELERY_RESULT_SERIALIZER="pickle",
)

# Discover and register tasks automatically in Django applications
# celery_app.autodiscover_tasks()
