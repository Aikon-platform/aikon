from django.db import models

from vhsapp.models.place import Place
from vhsapp.models.person import Person

from vhsapp.models.utils.functions import get_fieldname


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
    note = models.CharField(verbose_name=get_name("note"), max_length=500, unique=True)
