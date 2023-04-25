from django.db import models

from vhsapp.models.utils.functions import get_fieldname


def get_name(fieldname, plural=False):
    fields = {
        "source": {"en": "digitization source", "fr": "source de la numérisation"}
    }
    return get_fieldname(fieldname, fields, plural)


class Digitization(models.Model):
    class Meta:
        verbose_name = get_name("Digitization")
        verbose_name_plural = get_name("Digitization", True)

    def __str__(self):
        return ""  # TODO find a name

    # TODO: put back the methods and attributes of the old Digitization class
