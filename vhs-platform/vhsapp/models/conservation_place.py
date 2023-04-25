from django.db import models

from vhsapp.models.place import Place
from vhsapp.models.utils.constants import CONS_PLA
from vhsapp.models.utils.functions import get_fieldname


def get_name(fieldname, plural=False):
    fields = {
        "name": {"en": CONS_PLA, "fr": CONS_PLA},
        "city": {"en": "city", "fr": "ville"},
    }
    return get_fieldname(fieldname, fields, plural)


class ConservationPlace(models.Model):
    class Meta:
        verbose_name = get_name("ConservationPlace")
        verbose_name_plural = get_name("ConservationPlace", True)

    def __str__(self):
        return f"{self.city} | {self.name}"

    name = models.CharField(verbose_name=get_name("name"), max_length=200, unique=True)
    city = models.ForeignKey(
        Place,
        verbose_name=get_name("city"),
        blank=True,
        on_delete=models.SET_NULL,
        null=True,
    )
