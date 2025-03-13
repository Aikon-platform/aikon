from django.db import models

from app.webapp.models.utils.functions import get_fieldname


def get_name(fieldname, plural=False):
    fields = {
        "country": {"en": "country", "fr": "pays"},
        "latitude": {"en": "latitude", "fr": "latitude"},
        "longitude": {"en": "longitude", "fr": "longitude"},
    }
    return get_fieldname(fieldname, fields, plural)


class Place(models.Model):
    class Meta:
        verbose_name = get_name("Place")
        verbose_name_plural = get_name("Place", True)
        app_label = "webapp"

    def __str__(self, light=False):
        return f"{self.name}"  # , {self.country}"

    name = models.CharField(verbose_name=get_name("name"), max_length=200, unique=True)
    country = models.CharField(
        verbose_name=get_name("country"), max_length=150, blank=True
    )
    latitude = models.DecimalField(
        verbose_name=get_name("latitude"),
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True,
    )
    longitude = models.DecimalField(
        verbose_name=get_name("longitude"),
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True,
    )
