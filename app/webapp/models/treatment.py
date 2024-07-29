import importlib
import uuid

import requests
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import models

from app.config.settings import (
    APP_LANG,
    EMAIL_HOST_USER,
    APP_NAME,
    CV_API_URL,
    ADDITIONAL_MODULES,
)

from app.webapp.models.document_set import DocumentSet
from app.webapp.models.utils.constants import TRMT_TYPE
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
    requested_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, editable=False
    )
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
        choices=TRMT_TYPE,
    )

    document_set = models.ForeignKey(
        DocumentSet,
        related_name="treatments",  # to access all the treatments from DocumentSet
        verbose_name=get_name("DocumentSet"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    treated_objects = models.JSONField(blank=True, null=True)

    api_tracking_id = models.UUIDField(null=True, editable=False)

    def get_set(self, set_id):
        return self.set_id.all()

    def to_json(self):
        return {
            "id": self.id.__str__(),
            "type": self.task_type,
            "requested_on": self.requested_on,
            "requested_by": self.requested_by.__str__(),
            "treated_objects": self.treated_objects,
        }

    def save(self, *args, **kwargs):
        self.treated_objects = {
            "witnesses": {
                "total": len(self.document_set.wit_ids)
                if self.document_set.wit_ids
                else "0",
                "ids": self.document_set.wit_ids if self.document_set.wit_ids else None,
            },
            "series": {
                "total": len(self.document_set.ser_ids)
                if self.document_set.ser_ids
                else "0",
                "ids": self.document_set.ser_ids if self.document_set.ser_ids else None,
            },
            "works": {
                "total": len(self.document_set.work_ids)
                if self.document_set.work_ids
                else "0",
                "ids": self.document_set.work_ids
                if self.document_set.work_ids
                else None,
            },
            "digitizations": {
                "total": len(self.document_set.digit_ids)
                if self.document_set.digit_ids
                else "0",
                "ids": self.document_set.digit_ids
                if self.document_set.digit_ids
                else None,
            },
        }

        super().save(*args, **kwargs)

    def start_task(self, request, witnesses):
        """
        Start the task
        """
        if self.task_type in ADDITIONAL_MODULES:
            module_path = f"{self.task_type}.utils"
            module = importlib.import_module(module_path)

            prepare_request = getattr(module, "prepare_request")
            parameters = prepare_request(witnesses, self.id)

            if "message" in parameters.keys():
                self.on_task_success(  # Success because a message is returned if all of the documents were already treated
                    {
                        "notify": self.notify_email,
                        "message": parameters["message"],
                    },
                    request,
                )
                self.save()
                return

            try:
                api_query = requests.post(
                    url=f"{CV_API_URL}/{self.task_type}/start",
                    json=parameters,
                )
            except ConnectionError:
                log(f"[start_task] Connection error wit {CV_API_URL}")
                self.on_task_error(
                    {
                        "error": "API connection error",
                        "notify": self.notify_email,
                    },
                    request,
                )
                self.save()
                return

            try:
                api_response = api_query.json()
                log(
                    f"[start_task] {self.task_type} request sent to {CV_API_URL}: {api_response or ''}"
                )
                self.api_tracking_id = api_response["tracking_id"]
                self.status = "STARTED"

                flash_msg = (
                    "The requested task is underway. Please wait a few moments."
                    if APP_LANG == "en"
                    else "La tâche demandée est en cours. Veuillez patienter quelques instants."
                )
                messages.warning(request, flash_msg)

            except Exception as e:
                error = {
                    "source": "[start_task]",
                    "error_message": f"{self.task_type} request for treatment #{self.id} with status code: {api_query.status_code}",
                    "request_info": {
                        "method": "POST",
                        "url": f"{CV_API_URL}/{self.task_type}/start",
                        "payload": prepare_request(witnesses, self.id),
                    },
                    "response_info": {
                        "status_code": api_query.status_code,
                        "text": api_query.text or "",
                    },
                }

                log(error)
                self.on_task_error(
                    {
                        "error": "API error when starting requested task.",
                        "notify": self.notify_email,
                    },
                    request,
                )

        else:
            log(f"[start_task] Please install module for task {self.task_type}")
            self.on_task_error(
                {
                    "error": "Uninstalled module.",
                    "notify": self.notify_email,
                },
                request,
            )

        self.save()

    def on_task_success(self, data, request=None):
        """
        Handle the end of the task
        """
        self.terminate_task(
            "SUCCESS", message=data.get("message"), notify=data.get("notify")
        )

        if request:
            flash_msg = (
                f"The requested task was completed.\n{data.get('message') if data.get('message') else ''}"
                if APP_LANG == "en"
                else f"La tâche demandée a été complétée.\n{data.get('message') if data.get('message') else ''}"
            )
            messages.warning(request, flash_msg)

    def on_task_error(self, data, request=None):
        """
        Handle the end of the task
        """
        self.terminate_task(
            "ERROR", error=data.get("error", "Unknown error"), notify=data.get("notify")
        )

        if request:
            flash_msg = (
                f"The requested task could not be completed.\n{data.get('error', 'Unknown error')}"
                if APP_LANG == "en"
                else f"La tâche demandée n'a pas pu être complétée.\n{data.get('error', 'Unknown error')}"
            )
            messages.warning(request, flash_msg)

    def terminate_task(self, status="SUCCESS", error=None, message=None, notify=True):
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
                    f"[{APP_NAME.upper()} {self.task_type}] Task {self.status.lower()}",
                    f"Dear {APP_NAME.upper()} user,\n\nThe {self.task_type} task (#{self.id}) you requested on the {APP_NAME.upper()} platform was completed with the status {self.status}.\n\nErrors: {error if error else message}.\n\nBest,\nthe {APP_NAME.upper()} team.",
                    EMAIL_HOST_USER,
                    [self.requested_by.email],
                    fail_silently=False,
                )
            except Exception as e:
                log(
                    f"[treatment_email] Unable to send confirmation email for {self.requested_by.email}",
                    e,
                )

    def receive_notification(self, event, info):
        """
        Called by the API when tasks events happen
        """
        if event == "STARTED":
            self.status = "IN PROGRESS"
            self.save()
            return True
        elif event == "SUCCESS":
            data = {
                "notify": self.notify_email,
                "message": info,
            }
            self.on_task_success(data)
        elif event == "ERROR":
            data = {
                "notify": self.notify_email,
                "error": info,
            }
            self.on_task_error(data)
