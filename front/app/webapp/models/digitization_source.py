from django.db import models
from app.webapp.models.utils.functions import get_fieldname


def get_name(fieldname, plural=False):
    fields = {
        "DigitizationSource": {
            "en": "digitization source",
            "fr": "source de la numérisation",
        },
    }
    return get_fieldname(fieldname, fields, plural)


class DigitizationSource(models.Model):
    class Meta:
        verbose_name = get_name("DigitizationSource")
        verbose_name_plural = get_name("DigitizationSource", True)
        app_label = "webapp"

    def __str__(self, light=False):
        return self.source

    source = models.CharField(max_length=150, unique=True)
