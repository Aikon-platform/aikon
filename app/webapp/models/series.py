from django.db import models
from django.core.exceptions import ValidationError

from app.webapp.models.edition import Edition
from app.webapp.models.utils.functions import get_fieldname
from app.webapp.models.utils.constants import PUBLISHED_INFO, DATE_ERROR, DATE_INFO


def get_name(fieldname, plural=False):
    return get_fieldname(fieldname, {}, plural)


class Series(models.Model):
    class Meta:
        verbose_name = get_name("Series")
        verbose_name_plural = get_name("Series", True)
        app_label = "webapp"

    def __str__(self):
        return self.edition.name  # TODO find a name

    notes = models.TextField(verbose_name=get_name("notes"), max_length=500, blank=True)
    date_min = models.IntegerField(
        verbose_name=get_name("date_min"), null=True, blank=True, help_text=DATE_INFO
    )
    date_max = models.IntegerField(
        verbose_name=get_name("date_max"), null=True, blank=True
    )
    is_public = models.BooleanField(
        verbose_name=get_name("is_public"), default=False, help_text=PUBLISHED_INFO
    )
    edition = models.ForeignKey(
        Edition,
        verbose_name=get_name("Edition"),
        on_delete=models.SET_NULL,
        null=True,
    )

    def get_witnesses(self):
        return self.witness_set.all()

    def clean(self):
        # TODO: needs improvement
        super().clean()
        if self.date_min and self.date_max and self.date_min > self.date_max:
            raise ValidationError(DATE_ERROR)
