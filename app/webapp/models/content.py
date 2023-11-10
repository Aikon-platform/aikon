import re

from django.core.exceptions import ValidationError
from django.db import models

from app.webapp.models.witness import Witness
from app.webapp.models.work import Work
from app.webapp.models.place import Place
from app.webapp.models.language import Language

from app.webapp.models.utils.constants import TAG, PAG_ABBR, PAGE_ERROR
from app.webapp.models.utils.functions import get_fieldname
from app.webapp.utils.functions import format_start_end, extract_nb, validate_dates
from app.webapp.utils.logger import log


def get_name(fieldname, plural=False):
    fields = {
        "page_min": {"en": "From page/folio", "fr": "De la page/folio"},
        "page_max": {"en": "To page/folio", "fr": "Jusqu'à la page/folio"},
        "tags": {"en": f"{TAG}s", "fr": f"{TAG}s"},
        "place": {"en": "creation place", "fr": "lieu de création"},
    }
    return get_fieldname(fieldname, fields, plural)


def folios_to_pages(page: str = None):
    page_nb = extract_nb(page)
    if page_nb is None:
        return None
    if page.endswith("r"):
        return page_nb * 2 - 1
    if page.endswith("v"):
        return page_nb * 2
    return page_nb


def validate_page(page):
    match = re.match(r"^\d+[rv]?$", page)
    if not match:
        raise ValidationError(PAGE_ERROR)


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

    def get_witness(self) -> Witness | None:
        try:
            return self.witness
        except AttributeError:
            return None

    def get_pages(self):
        if self.page_min == "" and self.page_max == "":
            # TODO allow to use "-" to tell that a content takes all witness
            return ""

        return format_start_end(self.page_min, self.page_max)

    def get_nb_of_page(self, only_nb=True):
        wit = self.get_witness()
        p_min, p_max = folios_to_pages(self.page_min), folios_to_pages(self.page_max)
        if wit and p_min is not None and p_max is not None:
            page_t = "p" if wit.page_type == PAG_ABBR else "f"
            nb = p_max - p_min
            p_abbr = f"{page_t}{page_t}" if nb > 1 else page_t
            return nb if only_nb else f"{nb} {p_abbr}."

    def get_roles(self):
        # Django automatically creates a reverse relationship from Content to Role
        return self.roles.all()

    def clean(self):
        super().clean()
        validate_dates(self.date_min, self.date_max)

    def get_dates(self):
        return self.date_min or None, self.date_max or None
