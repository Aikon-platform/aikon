from django.db import models

from app.webapp.models.content import Content
from app.webapp.models.series import Series
from app.webapp.models.person import Person

from app.webapp.models.utils.functions import get_fieldname


def get_name(fieldname, plural=False):
    fields = {
        "source": {"en": "digitization source", "fr": "source de la numérisation"},
        "pub": {"en": "publisher", "fr": "éditeur/diffuseur"},
        "aut": {"en": "author", "fr": "auteur"},
        "ill": {"en": "illuminator", "fr": "enlumineur"},
        "sel": {"en": "bookseller", "fr": "libraire"},
    }
    return get_fieldname(fieldname, fields, plural)


ROLES = (
    ("pub", get_name("pub")),
    ("aut", get_name("aut")),
    ("ill", get_name("ill")),
    ("sel", get_name("sel")),
)


class Role(models.Model):
    class Meta:
        verbose_name = get_name("Role")
        verbose_name_plural = get_name("Role", True)
        app_label = "webapp"

    def __str__(self):
        return ""  # TODO find a name

    content = models.ForeignKey(
        Content,
        verbose_name=get_name("Content"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    series = models.ForeignKey(
        Series,
        verbose_name=get_name("Series"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    person = models.ForeignKey(
        Person,
        verbose_name=get_name("Person"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    role = models.CharField(
        verbose_name=get_name("Role"), choices=ROLES, max_length=150
    )
