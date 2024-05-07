# Table to track tasks : generate experiment id in the app, send it to API and retrieve it
# table with experiement ID, user id (foreign key) and status sent/processing/final/error
# Send email function as a method of the class
import uuid

from django.contrib.auth.models import User
from django.db import models

from app.config.settings import APP_LANG
from app.webapp.models.digitization import Digitization
from app.webapp.models.utils.functions import get_fieldname


def get_name(fieldname, plural=False):
    fields = {
        "APITask": {
            "en": "API task",
            "fr": "tâche API",
        },
    }
    return get_fieldname(fieldname, fields, plural)


class APITask(models.Model):
    class Meta:
        verbose_name = get_name("APITask")
        verbose_name_plural = get_name("APITask", True)
        app_label = "webapp"

    def __str__(self):
        space = "" if APP_LANG == "en" else " "
        return f"Task #{self.id}{space}: {self.experiment_id}"

    digitization = models.ForeignKey(
        Digitization,
        related_name="api_tasks",  # to access all the tasks from Digitization
        verbose_name=get_name("Digitization"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    experiment_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    task_type = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True, default="created")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)

    def get_digit(self):
        try:
            return self.digitization
        except AttributeError:
            return None

    def get_user(self):
        try:
            return self.user
        except AttributeError:
            return None

    def update_task(self):
        self.status = "running"
        self.save(update_fields=["status"])

    def complete_task(self):
        self.status = "completed"
        self.save(update_fields=["status"])

    def error_task(self):
        self.status = "error"
        self.save(update_fields=["status"])
