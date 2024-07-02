import uuid

import requests
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import models

from app.config.settings import (
    APP_LANG,
    EMAIL_HOST_USER,
    APP_URL,
    APP_NAME,
    CONTACT_MAIL,
    CV_API_URL,
)

from app.webapp.models.document_set import DocumentSet
from app.webapp.models.utils.functions import get_fieldname
from app.webapp.utils.logger import log


def get_name(fieldname, plural=False):
    fields = {
        "Treatment": {
            "en": "treatment",
            "fr": "traitement",
        },
    }
    return get_fieldname(fieldname, fields, plural)


class Treatment(models.Model):
    class Meta:
        verbose_name = get_name("Treatment")
        verbose_name_plural = get_name("Treatment", True)
        app_label = "webapp"

    def __str__(self):
        space = "" if APP_LANG == "en" else " "
        return f"Treatment #{self.id}{space}: {self.id}"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=20, default="Pending", editable=False)
    is_finished = models.BooleanField(default=False, editable=False)

    requested_on = models.DateTimeField(auto_now_add=True, editable=False)
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, editable=False)
    notify_email = models.BooleanField(
        default=True,
        verbose_name="Notify by email",
        blank=True,
        help_text="Send an email when the task is finished",
    )

    task_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=[  # TODO modifier pour peupler en fonction des apps installées
            ("extraction", "extraction"),
            ("similarity", "similarity"),
            ("vectorization", "vectorization"),
        ],
    )

    set_id = models.ForeignKey(
        DocumentSet,
        related_name="treatments",  # to access all the treatments from DocumentSet
        verbose_name=get_name("DocumentSet"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    treated_objects = models.JSONField(blank=True, null=True)

    api_tracking_id = models.UUIDField(null=True, editable=False)
    api_endpoint_prefix = task_type

    def start_task(self, tracking_id):
        """
        Start the task
        """
        try:
            self.api_tracking_id = tracking_id
            self.status = "STARTED"

        except Exception as e:
            log(
                f"[start_treatment] Request for task failed with an error",
                e,
            )
            self.status = "ERROR"
            self.is_finished = True

        self.save()

    def on_task_success(self, data):
        """
        Handle the end of the task
        """
        self.terminate_task("SUCCESS")

    def on_task_error(self, data):
        """
        Handle the end of the task
        """
        self.terminate_task("ERROR", data.get("error", "Unknown error"))

    def terminate_task(self, status="SUCCESS", error=None, notify=True):
        """
        Called when the task is finished
        """
        self.status = status
        if error:
            log(f"[treatment] Error: {error}")
        self.is_finished = True
        self.save()

        if notify and self.notify_email:
            try:
                send_mail(
                    f"[{APP_NAME.upper()} {self.task_type}] Task {self.status}",
                    f"Dear {APP_NAME.upper()} user,\n\nThe {self.task_type} task you requested was completed with the status {self.status}.\n\nYou can access the results on the platform: {APP_URL}/{APP_NAME}",
                    EMAIL_HOST_USER,
                    [self.requested_by.email],
                    fail_silently=False,
                )
            except Exception as e:
                log(
                    f"[treatment_email] Unable to send confirmation email for {self.requested_by.email}",
                    e,
                )

    def receive_notification(self, data: dict):
        """
        Called by the API when tasks events happen
        """
        event = data["event"]
        if event == "STARTED":
            self.status = "PROGRESS"
            self.save()
            return
        elif event == "SUCCESS":
            self.on_task_success(data)
        elif event == "ERROR":
            self.on_task_error(data)

    def get_progress(self):
        """
        Queries the API to get the task progress
        """
        try:
            api_query = requests.get(
                f"{CV_API_URL}/{self.api_endpoint_prefix}/{self.api_tracking_id}/status",
            )
        except ConnectionError:
            return {
                "status": "UNKNOWN",
                "error": "Connection error when getting task progress from the worker",
            }

        try:
            return {"status": self.status, **api_query.json()}
        except:
            log(f"[treatment] Error when reading task progress: {api_query.text}")
            return {
                "status": "UNKNOWN",
            }
