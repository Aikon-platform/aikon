from django.db import models

from vhsapp.models.place import Place
from vhsapp.models.person import Person

from vhsapp.models.utils.functions import get_fieldname


def get_name(fieldname, plural=False):
    fields = {
        "pub_place": {"en": "publication place", "fr": "lieu de publication"},
        "publisher": {"en": "publisher", "fr": "éditeur"},
    }
    return get_fieldname(fieldname, fields, plural)


class Edition(models.Model):
    class Meta:
        verbose_name = get_name("Edition")
        verbose_name_plural = get_name("Edition", True)

    def __str__(self):
        return ""  # TODO find a name

    pub_place = models.ForeignKey(
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
