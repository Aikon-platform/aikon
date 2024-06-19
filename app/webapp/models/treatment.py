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
    task_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=[
            ("regions", "regions"),
            ("similarity", "similarity"),
            ("vectorization", "vectorization"),
        ],
    )
    treatment_type = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        choices=[("auto", "auto"), ("manual", "manual")],
        default="auto",
    )
    status = models.CharField(max_length=50, blank=True, null=True, default="created")
    user_id = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    treated_object = models.ForeignKey(
        Digitization,
        related_name="treatments",  # to access all the treatments from Digitization
        verbose_name=get_name("Digitization"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    def get_object(self):
        try:
            return self.treated_object
        except AttributeError:
            return None

    def get_user(self):
        try:
            return self.user_id
        except AttributeError:
            return None

    def update_treatment(self):
        self.status = "running"
        self.save(update_fields=["status"])

    def complete_treatment(self, regions_ref):
        self.status = "completed"
        self.save(update_fields=["status"])
        self.completion_mail(regions_ref)

    def error_treatment(self, error_msg):
        self.status = "error"
        self.save(update_fields=["status"])
        self.error_mail(error_msg)

    def treatment_mail(self, message):
        try:
            send_mail(
                subject=f"[{APP_NAME.upper()} {self.task_type}] Your {self.task_type} treatment was completed!",
                message=message,
                from_email=EMAIL_HOST_USER,
                recipient_list=[self.user_id.email],
            )
        except Exception as e:
            log(
                f"[treatment_email] Unable to send confirmation email for {self.user_id.email}",
                e,
            )

    def completion_mail(self, regions_ref):
        if self.task_type == "regions":
            message = f"Dear {APP_NAME.upper()} user,\n\nThe {self.task_type} treatment you requested for {self.get_object()} was completed and your results were sent to the platform.\n\nSee the automatic results at: {APP_URL}/{APP_NAME}/{regions_ref}/show/"
        elif self.task_type == "similarity":
            message = (
                f"Dear {APP_NAME.upper()} user,\n\nThe {self.task_type} treatment you requested for {self.get_object()} was completed and your results were sent to the platform.\n\nSee the automatic results at: {APP_URL}/{APP_NAME}/{regions_ref}/show-similarity/",
            )
        else:
            message = f"Dear {APP_NAME.upper()} user,\n\nThe {self.task_type} treatment you requested for {self.get_object()} was completed and your results were sent to the platform."

        self.treatment_mail(message)

    def error_mail(self, error_msg):
        message = f"Dear {APP_NAME.upper()} user,\n\nThe {self.task_type} treatment you requested for {self.get_object()} could not be completed due to the following error: {error_msg}.\n\nYou can contact the administrator at {CONTACT_MAIL}."
        self.treatment_mail(message)
