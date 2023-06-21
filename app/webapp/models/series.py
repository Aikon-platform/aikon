from django.db import models

from app.webapp.models.edition import Edition

from app.webapp.models.utils.functions import get_fieldname
from app.webapp.models.utils.constants import PUBLISHED_INFO


def get_name(fieldname, plural=False):
    return get_fieldname(fieldname, {}, plural)


class Series(models.Model):
    class Meta:
        verbose_name = get_name("Series")
        verbose_name_plural = get_name("Series", True)
        app_label = "webapp"

    def __str__(self):
        return ""  # TODO find a name

    note = models.CharField(verbose_name=get_name("note"), max_length=500, unique=True)
    date_min = models.IntegerField(
        verbose_name=get_name("date_min"), null=True, blank=True
    )
    date_max = models.IntegerField(
        verbose_name=get_name("date_max"), null=True, blank=True
    )
    models.BooleanField(
        verbose_name=get_name("is_public"), default=False, help_text=PUBLISHED_INFO
    )
    edition = models.ForeignKey(
        Edition,
        verbose_name=get_name("Edition"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
