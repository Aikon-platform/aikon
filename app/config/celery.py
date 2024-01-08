import os
import sys
import environ
from celery import Celery

from app.webapp.utils.paths import BASE_DIR

# Django application configuration
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ENV = environ.Env()
environ.Env.read_env(env_file=f"{BASE_DIR}/config/.env")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.config.settings")

celery_app = Celery(
    "config",
    broker=f"redis://:{ENV('REDIS_PASSWORD')}@localhost:6379/0",
    backend=f"redis://:{ENV('REDIS_PASSWORD')}@localhost:6379/0",
    imports=("app.webapp.tasks",),
)

# Load Celery configuration from Django settings
celery_app.config_from_object("django.conf:settings", namespace="CELERY")

celery_app.conf.update(
    CELERY_ACCEPT_CONTENT=["json"],
    CELERY_TASK_SERIALIZER="json",
    CELERY_RESULT_SERIALIZER="json",
)

# Discover and register tasks automatically in Django applications
celery_app.autodiscover_tasks()
