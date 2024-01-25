from django.contrib.auth.models import User
from django.db import models
from django.utils.html import format_html

from app.webapp.models.conservation_place import ConservationPlace
from app.webapp.models.edition import Edition
from app.webapp.models.tag import Tag
from app.webapp.models.utils.functions import get_fieldname
from app.webapp.models.utils.constants import PUBLISHED_INFO, DATE_INFO
from app.webapp.models.work import Work
from app.webapp.utils.functions import validate_dates


def get_name(fieldname, plural=False):
    fields = {
        "notes": {"en": "additional notes", "fr": "éléments descriptifs du contenu"},
        "vol_nb": {"en": "volume n°", "fr": "volume n°"},
        "no_vol_nb": {
            "en": "No volume number provided",
            "fr": "Pas de numéro de volume renseigné",
        },
    }
    return get_fieldname(fieldname, fields, plural)


class Series(models.Model):
    class Meta:
        verbose_name = get_name("Series")
        verbose_name_plural = get_name("Series", True)
        app_label = "webapp"

    def __str__(self):
        return self.edition.name  # TODO find a name

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(verbose_name=get_name("notes"), max_length=600, blank=True)
    date_min = models.IntegerField(
        verbose_name=get_name("date_min"), null=True, blank=True, help_text=DATE_INFO
    )
    date_max = models.IntegerField(
        verbose_name=get_name("date_max"), null=True, blank=True
    )
    is_public = models.BooleanField(
        verbose_name=get_name("is_public"), default=False, help_text=PUBLISHED_INFO
    )
    edition = models.ForeignKey(
        Edition,
        verbose_name=get_name("Edition"),
        on_delete=models.SET_NULL,
        null=True,
    )
    work = models.ForeignKey(
        Work,
        verbose_name=get_name("Work"),
        on_delete=models.SET_NULL,
        null=True,
    )
    place = models.ForeignKey(
        ConservationPlace,
        verbose_name=get_name("ConservationPlace"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name=get_name("Tag"),
        blank=True,
    )

    def get_witnesses(self):
        return self.witness_set.all()

    def get_works(self):
        return [
            content.work
            for witness in self.get_witnesses()
            for content in witness.get_contents()
            if content.work is not None
        ]

    def get_work_titles(self):
        works = self.get_works()
        return format_html(
            "<br>".join([work.__str__() for work in works]) if len(works) else "-"
        )

    def get_roles(self):
        return self.roles.all()

    def get_person_names(self):
        roles = self.get_roles()
        if len(roles) == 0:
            return "-"
        return format_html("<br>".join([role.__str__() for role in roles]))

    def clean(self):
        super().clean()
        validate_dates(self.date_min, self.date_max)
