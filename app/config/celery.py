import os
import sys

import django
import environ
from celery import Celery

from app.webapp.utils.paths import BASE_DIR

# Django application configuration
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ENV = environ.Env()
environ.Env.read_env(env_file=f"{BASE_DIR}/config/.env")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.config.settings")
django.setup()

app = Celery("config")

# Load Celery configuration from Django settings
app.config_from_object("django.conf:settings", namespace="CELERY")

# TODO: set REDIS_PASSWORD again
# app.conf.broker_url = f"redis://:{ENV('REDIS_PASSWORD')}@localhost:6379/0"
# app.conf.update(
#     CELERY_RESULT_BACKEND=f"redis://:{ENV('REDIS_PASSWORD')}@localhost:6379/0",
#     CELERY_ACCEPT_CONTENT=["json"],
#     CELERY_TASK_SERIALIZER="json",
#     CELERY_RESULT_SERIALIZER="json",
# )
app.conf.broker_url = "redis://localhost:6379/0"
app.conf.update(
    CELERY_RESULT_BACKEND="redis://localhost:6379/0",
    CELERY_ACCEPT_CONTENT=["json"],
    CELERY_TASK_SERIALIZER="json",
    CELERY_RESULT_SERIALIZER="json",
)


# Discover and register tasks automatically in Django applications
app.autodiscover_tasks()
