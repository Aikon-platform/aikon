import re

from django.db import models

from app.webapp.models.witness import Witness
from app.webapp.models.work import Work
from app.webapp.models.place import Place
from app.webapp.models.language import Language

from app.webapp.models.utils.constants import CONT, WIT, WORK, TAG
from app.webapp.models.utils.functions import get_fieldname
from app.webapp.utils.functions import format_start_end


def get_name(fieldname, plural=False):
    fields = {
        "page_min": {"en": "From page/folio", "fr": "De la page/folio"},
        "page_max": {"en": "To page/folio", "fr": "Jusqu'à la page/folio"},
        "tags": {"en": f"{TAG}s", "fr": f"{TAG}s"},
        "place": {"en": "creation place", "fr": "lieu de création"},
    }
    return get_fieldname(fieldname, fields, plural)


def folios_to_pages(page: str):
    page_nb = int(page.replace("r", "").replace("v", ""))
    if page.endswith("r"):
        return page_nb * 2 - 1
    if page.endswith("v"):
        return page_nb * 2
    return page_nb


def validate_page(page):
    match = re.match(r"^\d+[rv]?$", page)
    return match is not None


class Content(models.Model):
    class Meta:
        verbose_name = get_name("Content")
        verbose_name_plural = get_name("Content", True)
        app_label = "webapp"

    def __str__(self):
        return f"{self.witness.__str__()} ({self.get_pages()})"

    witness = models.ForeignKey(
        Witness,
        related_name="contents",  # to access the related contents from Witness: witness.contents.all()
        verbose_name=get_name("Witness"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    work = models.ForeignKey(
        Work,
        verbose_name=get_name("Work"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    place = models.ForeignKey(
        Place,
        verbose_name=get_name("place"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    lang = models.ForeignKey(
        Language,
        verbose_name=get_name("Language"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    date_min = models.IntegerField(
        verbose_name=get_name("date_min"), null=True, blank=True
    )
    date_max = models.IntegerField(
        verbose_name=get_name("date_max"), null=True, blank=True
    )
    page_min = models.CharField(
        verbose_name=get_name("page_min"),
        null=True,
        blank=True,
        max_length=15,
        validators=[validate_page],
    )
    page_max = models.CharField(
        verbose_name=get_name("page_max"),
        null=True,
        blank=True,
        max_length=15,
        validators=[validate_page],
    )

    def get_pages(self):
        return format_start_end(self.page_min, self.page_max)

    def get_roles(self):
        # Django automatically creates a reverse relationship from Content to Role
        return self.role_set.all()
