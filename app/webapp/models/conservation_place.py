from django.db import models

from app.webapp.models.place import Place
from app.webapp.models.utils.constants import CONS_PLA
from app.webapp.models.utils.functions import get_fieldname


def get_name(fieldname, plural=False):
    fields = {
        "name": {"en": CONS_PLA, "fr": CONS_PLA},
        "city": {"en": "city", "fr": "ville"},
        "licence": {"en": "licence", "fr": "licence"},
        "licence_info": {
            "en": "URL mentioning reproduction rights",
            "fr": "URL précisant les droits de reproduction",
        },
    }
    return get_fieldname(fieldname, fields, plural)


class ConservationPlace(models.Model):
    class Meta:
        verbose_name = get_name("ConservationPlace")
        verbose_name_plural = get_name("ConservationPlace", True)
        app_label = "webapp"

    def __str__(self):
        if self.city:
            return f"{self.city} | {self.name}"
        return self.name

    name = models.CharField(verbose_name=get_name("name"), max_length=200, unique=True)
    city = models.ForeignKey(
        Place,
        verbose_name=get_name("city"),
        blank=True,
        on_delete=models.SET_NULL,
        null=True,
    )
    licence = models.URLField(
        verbose_name=get_name("licence"),
        blank=True,
        null=True,
        # TODO add licence_info inside the form
    )

    def get_licence(self):
        return (
            self.licence or "Do not reuse"
        )  # TODO create page to redirect to in order to explicit what is "no reuse"
