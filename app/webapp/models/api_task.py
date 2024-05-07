# Table to track tasks : generate experiment id in the app, send it to API and retrieve it
# table with experiement ID, user id (foreign key) and status sent/processing/final/error
# Send email function as a method of the class
import uuid

from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import models

from app.config.settings import (
    APP_LANG,
    EMAIL_HOST_USER,
    APP_URL,
    APP_NAME,
    CONTACT_MAIL,
)
from app.webapp.models.digitization import Digitization
from app.webapp.models.utils.functions import get_fieldname
from app.webapp.utils.logger import log


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

    def complete_task(self, anno_ref):
        self.status = "completed"
        self.save(update_fields=["status"])
        self.completion_mail(anno_ref)

    def error_task(self, error_msg):
        self.status = "error"
        self.save(update_fields=["status"])
        self.error_mail(error_msg)

    def task_mail(self, message):
        try:
            send_mail(
                subject=f"[{APP_NAME} {self.task_type}] Your {self.task_type} task was completed!",
                message=message,
                from_email=EMAIL_HOST_USER,
                recipient_list=[self.user.email],
            )
        except Exception as e:
            log(
                f"[task_email] Unable to send confirmation email for {self.user.email}",
                e,
            )

    def completion_mail(self, anno_ref):
        if self.task_type == "extraction":
            message = f"Dear {APP_NAME} user,\n\nThe {self.task_type} task you requested for {self.get_digit()} was completed and your results were sent to the platform.\n\nSee the automatic results at: {APP_URL}/{APP_NAME}/{anno_ref}/show/"
        elif self.task_type == "similarity":
            message = (
                f"Dear {APP_NAME} user,\n\nThe {self.task_type} task you requested for {self.get_digit()} was completed and your results were sent to the platform.\n\nSee the automatic results at: {APP_URL}/{APP_NAME}/{anno_ref}/show-similarity/",
            )
        else:
            message = f"Dear {APP_NAME} user,\n\nThe {self.task_type} task you requested for {self.get_digit()} was completed and your results were sent to the platform."

        self.task_mail(message)

    def error_mail(self, error_msg):
        message = f"Dear {APP_NAME} user,\n\nThe {self.task_type} task you requested for {self.get_digit()} could not be completed due to the following error: {error_msg}.\n\nYou can contact the administrator at {CONTACT_MAIL}."
        self.task_mail(message)
