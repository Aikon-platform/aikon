import importlib
import uuid
import requests

from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from app.config.settings import (
    APP_LANG,
    EMAIL_HOST_USER,
    APP_NAME,
    CV_API_URL,
    ADDITIONAL_MODULES,
)

from app.webapp.models.document_set import DocumentSet
from app.webapp.models.searchable_models import AbstractSearchableModel, json_encode
from app.webapp.models.utils.constants import TRMT_TYPE, TRMT_STATUS, NO_USER
from app.webapp.models.utils.functions import get_fieldname
from app.webapp.tasks import get_all_witnesses

from app.webapp.utils.logger import log


def get_name(fieldname, plural=False):
    fields = {
        "id": {"en": "Identification number", "fr": "Identifiant"},
        "status": {"en": "task status", "fr": "statut de la tâche"},
        "is_finished": {"en": "finished", "fr": "tâche achevée"},
        "requested_on": {"en": "requested on", "fr": "demandé le"},
        "requested_by": {"en": "requested by", "fr": "demandé par"},
        "task_type": {"en": "task type", "fr": "type de tâche"},
        "treated_objects": {"en": "treated objects", "fr": "objets traités"},
        "api_tracking_id": {"en": "API identification number", "fr": "Identifiant API"},
        "notify_email": {"en": "notify by email", "fr": "Notifier par email"},
    }
    return get_fieldname(fieldname, fields, plural)


class Treatment(AbstractSearchableModel):
    class Meta:
        verbose_name = get_name("Treatment")
        verbose_name_plural = get_name("Treatment", True)
        app_label = "webapp"

    def __str__(self, light=False):
        task = f"{self.task_type.__str__().capitalize()}"
        if light:
            if self.json and "title" in self.json:
                return self.json["title"]
            return task

        if self.document_set:
            return f"{task} | {self.document_set.title}"
        return task

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(
        max_length=50,
        default="PENDING",
        choices=TRMT_STATUS,
    )
    is_finished = models.BooleanField(default=False, editable=False)

    requested_on = models.DateTimeField(auto_now_add=True, editable=False, null=True)
    requested_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, editable=False
    )
    notify_email = models.BooleanField(
        default=True,
        verbose_name=get_name("notify_email"),
        blank=True,
        help_text="Send an email when the task is finished"
        if APP_LANG == "en"
        else "Envoyer un email lorsque la tâche est terminée",
    )

    task_type = models.CharField(
        max_length=50,
        verbose_name=get_name("task_type"),
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

    _internal_save = False

    def get_objects_name(self):
        if not self.document_set:
            return []
        # TODO display treated_objects instead of document_set ?
        return self.document_set.document_names

    def get_objects(self):
        if not self.document_set:
            return []
        # TODO display treated_objects instead of document_set ?
        return self.document_set.documents

    def get_witnesses(self):
        if not self.document_set:
            return []
        # TODO display treated_objects instead of document_set ?
        return self.document_set.all_witnesses()

    def get_cancel_url(self):
        return f"{CV_API_URL}/{self.task_type}/{self.api_tracking_id}/cancel"

    def get_query_parameters(self):
        if not self.document_set:
            return ""
        return f"?document_set={self.document_set.id}&task_type={self.task_type}&notify_email={self.notify_email}"

    def get_absolute_url(self):
        return reverse("webapp:treatment_view", args=[self.id])

    def get_treated_url(self):
        urls = []
        if not self.document_set:
            return urls
        witnesses = self.document_set.all_witness_ids()
        urls.append(
            [reverse("webapp:witness_regions_view", args=[wid]) for wid in witnesses]
        )
        #  TODO make variable used in svelte component and in overall app
        tabs = {
            "regions": "page",
            "similarity": "similarity",
            "vectorization": "vectorization",
        }

        if self.task_type in tabs.keys():
            urls = [f"{url}?tab={tabs[self.task_type]}" for url in urls]
        return urls

    def to_json(self, reindex=True):
        try:
            user = self.requested_by
            doc_set = self.document_set
            req_on = self.requested_on
            return json_encode(
                {
                    "id": self.id.__str__(),
                    "class": self.__class__.__name__,
                    "type": get_name("Treatment"),
                    "title": self.__str__(),
                    "updated_at": req_on.strftime("%Y-%m-%d %H:%M") if req_on else None,
                    "url": self.get_absolute_url(),
                    "user": user.__str__() if user else NO_USER,
                    "user_id": user.id if user else 0,
                    "status": self.status,
                    "is_finished": self.is_finished,
                    "treated_objects": self.treated_objects,
                    "cancel_url": self.get_cancel_url(),
                    "query_parameters": self.get_query_parameters(),
                    "api_tracking_id": self.api_tracking_id,
                    "selection": {
                        "id": doc_set.id if doc_set else None,
                        "type": "Treatment",
                        "title": self.__str__(),
                        "selected": doc_set.get_document_metadata()
                        if doc_set
                        else None,
                    },
                }
            )
        except Exception as e:
            log(f"[treatment_to_json] Error", e)
            return None

    def save(self, *args, **kwargs):
        if not self._internal_save:
            self._internal_save = True
            print(f"Saving Treatment {self.id}")

            user = kwargs.pop("user", None)
            if not self.requested_by and user:
                self.requested_by = user

            if not self.document_set:
                log(
                    f"[treatment_save] No document set for treatment {self.id}, aborting."
                )
                self.status = "ERROR"
                super().save(*args, **kwargs)
                return

            self.treated_objects = {
                "witnesses": {
                    "total": len(self.document_set.wit_ids or []),
                    "ids": self.document_set.wit_ids or None,
                },
                "series": {
                    "total": len(self.document_set.ser_ids or []),
                    "ids": self.document_set.ser_ids or None,
                },
                "works": {
                    "total": len(self.document_set.work_ids or []),
                    "ids": self.document_set.work_ids or None,
                },
                "digitizations": {
                    "total": len(self.document_set.digit_ids or []),
                    "ids": self.document_set.digit_ids or None,
                },
            }

        super().save(*args, **kwargs)

    def start_task(self, witnesses):
        """Start the task"""
        if self.task_type not in ADDITIONAL_MODULES:
            log(f"[start_task] Uninstalled module: {self.task_type}")
            return

        try:
            module = importlib.import_module(f"{self.task_type}.utils")
            parameters = getattr(module, "prepare_request")(witnesses, self.id)
        except (ImportError, AttributeError) as e:
            log(f"[start_task] Error loading module: {e}")
            self.on_task_error(
                {"error": "Module loading error.", "notify": self.notify_email}
            )
            self.save()
            return

        if "message" in parameters:
            self.on_task_success(
                {"notify": self.notify_email, "message": parameters["message"]}
            )
            self.save()
            return

        try:
            api_query = requests.post(
                f"{CV_API_URL}/{self.task_type}/start", json=parameters
            )
            if (
                api_query.status_code != 200
                or api_query.headers.get("Content-Type") != "application/json"
            ):
                raise ValueError(f"Unexpected response: {api_query.text}")

            api_response = api_query.json()

            self.api_tracking_id = api_response["tracking_id"]
            self.status = "STARTED"

            log(f"[start_task] Task {self.task_type} started: {api_response}")

        except (requests.RequestException, ValueError, KeyError) as e:
            log(
                {
                    "source": "[start_task]",
                    "error_message": f"{self.task_type} request failed with status: {api_query.status_code}",
                    "request_info": {
                        "method": "POST",
                        "url": f"{CV_API_URL}/{self.task_type}/start",
                        "payload": parameters,
                    },
                    "response_info": {"text": api_query.text, "error": str(e)},
                }
            )
            self.on_task_error(
                {"error": "API error when starting task.", "notify": self.notify_email}
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
                    f"Dear {APP_NAME.upper()} user,\n\nThe {self.task_type} task (#{self.id}) you requested on the {APP_NAME.upper()} platform was completed with the status {self.status}.\n\nMessage: {error if error else message}.\n\nBest,\nthe {APP_NAME.upper()} team.",
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


@receiver(post_save, sender=Treatment)
def treatment_post_save(sender, instance, created, **kwargs):
    if created:
        get_all_witnesses.delay(instance)
