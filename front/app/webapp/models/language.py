from django.db import models

from app.webapp.models.utils.functions import get_fieldname


def get_name(fieldname, plural=False):
    fields = {
        "lang": {"en": "language", "fr": "langue"},
        "code": {"en": "code", "fr": "code"},
    }
    return get_fieldname(fieldname, fields, plural)


class Language(models.Model):
    class Meta:
        verbose_name = get_name("Language")
        verbose_name_plural = get_name("Language", True)
        app_label = "webapp"

    def __str__(self, light=False):
        return self.lang

    lang = models.CharField(verbose_name=get_name("lang"), max_length=200, unique=True)
    code = models.CharField(verbose_name=get_name("code"), max_length=200, unique=True)
