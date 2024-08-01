from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.db import models

from app.webapp.models.digitization import Digitization
from app.webapp.models.series import Series
from app.webapp.models.utils.functions import get_fieldname
from django.urls import reverse

from app.webapp.models.witness import Witness
from app.webapp.models.work import Work


def get_name(fieldname, plural=False):
    fields = {
        "DocumentSet": {
            "en": "document set",
            "fr": "panier de documents",
        },
    }
    return get_fieldname(fieldname, fields, plural)


class DocumentSet(models.Model):
    class Meta:
        verbose_name = get_name("DocumentSet")
        verbose_name_plural = get_name("DocumentSet", True)
        app_label = "webapp"

    def __str__(self):
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

    def get_absolute_url(self):
        # TODO create view to edit document set without loading it
        # return reverse("document_set", args=[self.id])
        return ""

    def get_witnesses(self):
        if not self.wit_ids:
            return []
        return list(Witness.objects.filter(id__in=self.wit_ids))

    def get_series(self):
        if not self.ser_ids:
            return []
        return list(Series.objects.filter(id__in=self.ser_ids))

    def get_digits(self):
        if not self.digit_ids:
            return []
        return list(Digitization.objects.filter(id__in=self.digit_ids))

    def get_works(self):
        if not self.work_ids:
            return []
        return list(Work.objects.filter(id__in=self.work_ids))

    def get_str_documents(self):
        pass

    def to_json(self):
        return {
            "id": self.id,
            "class": self.__class__.__name__,
            "type": get_name("Treatment"),
            "title": self.__str__(),
            "user_id": self.user.id,
            "user": self.user.__str__(),
            "url": self.get_absolute_url(),
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M"),
            "is_public": self.is_public,
            # "metadata": {
            #     get_name("id_nb"): self.id_nb or "-",
            #     get_name("Work"): self.get_work_titles(),
            #     get_name("place_name"): self.get_place_names(),
            #     get_name("dates"): format_dates(*self.get_dates()),
            #     get_name("page_nb"): self.get_page(),
            #     get_name("Language"): self.get_lang_names(),
            # },
            # "buttons": buttons,
        }
