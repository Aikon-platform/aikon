from django.core.exceptions import ValidationError
from django.db import models

from app.webapp.models.place import Place
from app.webapp.models.person import Person
from app.webapp.models.tag import Tag
from app.webapp.models.utils.constants import DATE_ERROR

from app.webapp.models.utils.functions import get_fieldname
from app.webapp.utils.functions import validate_dates


def get_name(fieldname, plural=False):
    fields = {
        "place": {"en": "creation place", "fr": "lieu de création"},
        "author": {"en": "author", "fr": "auteur"},
    }
    return get_fieldname(fieldname, fields, plural)


class Work(models.Model):
    class Meta:
        verbose_name = get_name("Work")
        verbose_name_plural = get_name("Work", True)
        app_label = "webapp"

    def __str__(self):
        return self.title

    title = models.CharField(
        verbose_name=get_name("title"), max_length=600, unique=True
    )
    date_min = models.IntegerField(
        verbose_name=get_name("date_min"), null=True, blank=True
    )
    date_max = models.IntegerField(
        verbose_name=get_name("date_max"), null=True, blank=True
    )
    place = models.ForeignKey(
        Place,
        verbose_name=get_name("place"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    author = models.ForeignKey(
        Person,
        verbose_name=get_name("author"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    notes = models.TextField(
        verbose_name=get_name("notes"),
        max_length=1000,
        blank=True,
        null=True,
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name=get_name("Tag"),
        blank=True,
    )

    def clean(self):
        super().clean()
        validate_dates(self.date_min, self.date_max)
