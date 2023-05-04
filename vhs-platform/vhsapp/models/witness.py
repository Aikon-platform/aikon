from django.db import models
from django.contrib.auth.models import User

from vhsapp.models.conservation_place import ConservationPlace
from vhsapp.models.utils.constants import MS, VOL, WIT, WIT_TYPE, SER
from vhsapp.models.utils.functions import get_fieldname


def get_name(fieldname, plural=False):
    fields = {
        "id_nb": {"en": "identification number", "fr": "cote"},
        "nb_pages": {"en": "number of pages/folios", "fr": "nombre de pages/folios"},
        "link": {
            "en": "external link (online catalog, etc.)",
            "fr": "lien externe (catalogue en ligne, etc.)",
        },
        "is_paginated": {"en": "Paginated?", "fr": "Paginé ?"},
        "volume": {"en": VOL, "fr": "tome"},
        "series": {"en": SER, "fr": "série"},
    }

    return get_fieldname(fieldname, fields, plural)


class Witness(models.Model):
    class Meta:
        verbose_name = get_name("Witness")
        verbose_name_plural = get_name("Witness", True)

    def __str__(self):
        return ""  # TODO find a name

    type = models.CharField(
        verbose_name=get_name("type"), choices=WIT_TYPE, max_length=150
    )
    id_nb = models.CharField(verbose_name=get_name("id_nb"), max_length=150)
    place = models.ForeignKey(
        ConservationPlace,
        verbose_name=get_name("ConservationPlace"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    # TODO nb_pages, title, link, is_paginated, is_public, volume, series
    note = models.CharField(verbose_name=get_name("note"), max_length=500, unique=True)

    def get_metadata(self):
        metadata = {
            "Place of conservation": self.place,
            "Reference number": self.id_nb,
        }
        if note := self.note:
            metadata["Notes"] = note

        return metadata

    def get_contents(self):
        # method to retrieve
        return self.contents.all()
