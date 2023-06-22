from django.db import models

from app.webapp.models.utils.functions import get_fieldname


def get_name(fieldname, plural=False):
    return get_fieldname(fieldname, {}, plural)


class Person(models.Model):
    class Meta:
        verbose_name = get_name("Person")
        verbose_name_plural = get_name("Person", True)
        app_label = "webapp"

    def __str__(self):
        return self.name

    name = models.CharField(verbose_name=get_name("name"), max_length=200, unique=True)
    date_min = models.IntegerField(
        verbose_name=get_name("date_min"), null=True, blank=True
    )
    date_max = models.IntegerField(
        verbose_name=get_name("date_max"), null=True, blank=True
    )
