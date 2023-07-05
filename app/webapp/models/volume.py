from django.db import models

from app.webapp.models.edition import Edition

from app.webapp.models.utils.functions import get_fieldname


def get_name(fieldname, plural=False):
    fields = {
        "number": {"en": "volume number", "fr": "numéro de tome"},
        "number_info": {
            "en": "number useful for classifying the different volumes of an edition, but not necessarily of historical value",
            "fr": "numéro utile pour classer les différents tomes d'une édition, mais qui n'a pas nécessairement de valeur historique",
        },
    }
    return get_fieldname(fieldname, fields, plural)


class Volume(models.Model):
    class Meta:
        verbose_name = get_name("Volume")
        verbose_name_plural = get_name("Volume", True)
        app_label = "webapp"

    def __str__(self):
        return self.title

    title = models.CharField(
        verbose_name=get_name("title"), max_length=150, unique=True
    )
    number = models.IntegerField(
        verbose_name=get_name("number"),
        help_text=get_name("number_info"),
        blank=True,
        null=True,
    )
    edition = models.ForeignKey(
        Edition,
        verbose_name=get_name("Edition"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
