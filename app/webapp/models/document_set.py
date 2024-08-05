from functools import lru_cache

from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.db import models

from app.webapp.models.digitization import Digitization
from app.webapp.models.series import Series
from app.webapp.models.utils.functions import get_fieldname
from django.urls import reverse

from app.webapp.models.witness import Witness
from app.webapp.models.work import Work
from app.webapp.utils.functions import get_summary


def get_name(fieldname, plural=False):
    fields = {
        "DocumentSet": {
            "en": "document set",
            "fr": "set de documents",
        },
    }
    return get_fieldname(fieldname, fields, plural)


class DocumentSet(models.Model):
    class Meta:
        verbose_name = get_name("DocumentSet")
        verbose_name_plural = get_name("DocumentSet", True)
        app_label = "webapp"

    def __str__(self):
        if self.length() != 1:
            return f"{self.title} ({self.length()} documents)"
        if self.wit_ids:
            return f"{self.witnesses[0]}"
        if self.ser_ids:
            return f"{self.series[0]}"
        if self.digit_ids:
            return f"{self.digits[0]}"
        if self.work_ids:
            return f"{self.works[0]}"
        return self.title

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    title = models.CharField(max_length=50)
    is_public = models.BooleanField(default=False)

    wit_ids = ArrayField(models.IntegerField(), default=list, blank=True, null=True)
    ser_ids = ArrayField(models.IntegerField(), default=list, blank=True, null=True)
    digit_ids = ArrayField(models.IntegerField(), default=list, blank=True, null=True)
    work_ids = ArrayField(models.IntegerField(), default=list, blank=True, null=True)

    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)

    selection = models.JSONField(
        verbose_name="JSON selection",
        blank=True,
        null=True,
    )

    def length(self):
        return sum(
            len(field or [])
            for field in (self.wit_ids, self.ser_ids, self.digit_ids, self.work_ids)
        )

    def get_treatments(self):
        return self.treatments.all()

    @property
    def witnesses(self):
        if not self.wit_ids:
            return []
        return list(Witness.objects.filter(id__in=self.wit_ids).select_related("place"))

    @property
    def series(self):
        if not self.ser_ids:
            return []
        return list(
            Series.objects.filter(id__in=self.ser_ids).select_related("edition")
        )

    @property
    def digits(self):
        if not self.digit_ids:
            return []
        return list(
            Digitization.objects.filter(id__in=self.digit_ids).select_related("witness")
        )

    @property
    def works(self):
        if not self.work_ids:
            return []
        return list(Work.objects.filter(id__in=self.work_ids).select_related("author"))

    @property
    def documents(self):
        return self.witnesses + self.series + self.digits + self.works

    @property
    def document_names(self):
        return [obj.__str__() for obj in self.documents]

    @lru_cache(maxsize=None)
    def get_all_witnesses(self):
        witness_ids = set(self.wit_ids or [])
        for series in self.series:
            witness_ids.update(series.wit_ids or [])
        for work in self.works:
            witness_ids.update(work.wit_ids or [])
        return list(
            Witness.objects.filter(id__in=witness_ids).select_related("relevant_field")
        )

    def get_document_metadata(self):
        def obj_meta(obj):
            return {"id": obj.id, "title": obj.__str__(), "url": obj.get_absolute_url()}

        return {
            "Witness": {wit.id: obj_meta(wit) for wit in self.witnesses},
            "Series": {ser.id: obj_meta(ser) for ser in self.series},
            "Digitization": {digit.id: obj_meta(digit) for digit in self.digits},
            "Work": {work.id: obj_meta(work) for work in self.works},
        }

    def get_treatment_metadata(self):
        def meta(treatment):
            return {
                "id": treatment.id.__str__(),
                "status": treatment.status,
                "task_type": treatment.task_type,
                "url": treatment.get_absolute_url(),
            }

        return {
            treatment.id.__str__(): meta(treatment)
            for treatment in self.get_treatments()
        }

    def get_absolute_url(self):
        # TODO create view to edit document set without loading it
        # return reverse("document_set", args=[self.id])
        return ""

    def to_json(self):
        user = self.user
        return {
            "id": self.id,
            "class": self.__class__.__name__,
            "type": get_name("DocumentSet"),
            "title": self.__str__(),
            "user_id": user.id if user else "None",
            "user": user.__str__() if user else "None",
            "url": self.get_absolute_url(),
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M")
            if self.updated_at
            else "None",
            "is_public": self.is_public,
            "selection": {
                "id": self.id,
                "type": "documentSet",
                "title": self.title,
                "selected": self.get_document_metadata(),
            },
            "treatments": self.get_treatment_metadata(),
        }
