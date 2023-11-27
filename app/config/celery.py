import os
from celery import Celery

# Django application configuration
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")

# Load Celery configuration from Django settings
app.config_from_object("django.conf:settings", namespace="CELERY")

# Discover and register tasks automatically in Django applications
app.autodiscover_tasks()
