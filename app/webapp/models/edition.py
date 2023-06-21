from django.db import models

from app.webapp.models.place import Place
from app.webapp.models.person import Person

from app.webapp.models.utils.functions import get_fieldname


def get_name(fieldname, plural=False):
    fields = {
        "pub_place": {"en": "publication place", "fr": "lieu de publication"},
        "publisher": {"en": "publisher", "fr": "éditeur"},
        "name_info": {
            "en": "name without historical value, useful to distinguish several editions sharing date and place of publication",
            "fr": "nom sans valeur historique, utile pour distinguer plusieurs éditions partageant date et lieu de publication",
        },
    }
    return get_fieldname(fieldname, fields, plural)


class Edition(models.Model):
    class Meta:
        verbose_name = get_name("Edition")
        verbose_name_plural = get_name("Edition", True)
        app_label = "webapp"

    def __str__(self):
        return ""  # TODO find a name

    name = models.CharField(
        verbose_name=get_name("name"),
        max_length=500,
        help_text=get_name("name_info"),
        unique=True,
    )

    place = models.ForeignKey(
        Place,
        verbose_name=get_name("pub_place"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    publisher = models.ForeignKey(
        Person,
        verbose_name=get_name("publisher"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
