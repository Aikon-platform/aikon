import os
import sys
import environ
from celery import Celery

from app.webapp.utils.paths import BASE_DIR

# Django application configuration
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ENV = environ.Env()
environ.Env.read_env(env_file=f"{BASE_DIR}/config/.env")
DEBUG = ENV.bool("DEBUG")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.config.settings")

redis_prefix = "redis://" if DEBUG else f"redis://:{ENV('REDIS_PASSWORD')}@"

celery_app = Celery(
    "config",
    broker=f"{redis_prefix}localhost:6379/0",
    backend=f"{redis_prefix}localhost:6379/0",
    imports=("app.webapp.tasks",),
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
celery_app.autodiscover_tasks()
