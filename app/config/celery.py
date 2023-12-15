import os
import sys

from celery import Celery

# Django application configuration
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.config.settings")

app = Celery("config")

# Load Celery configuration from Django settings
app.config_from_object("django.conf:settings", namespace="CELERY")

# Discover and register tasks automatically in Django applications
app.autodiscover_tasks()
