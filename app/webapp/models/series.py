from django.contrib.auth.models import User
from django.db import models
from django.utils.html import format_html

from app.webapp.models.conservation_place import ConservationPlace
from app.webapp.models.edition import Edition
from app.webapp.models.tag import Tag
from app.webapp.models.utils.functions import get_fieldname
from app.webapp.models.utils.constants import PUBLISHED_INFO, DATE_INFO
from app.webapp.models.work import Work
from app.webapp.utils.constants import TRUNCATEWORDS
from app.webapp.utils.functions import validate_dates, truncate_words, format_dates


def get_name(fieldname, plural=False):
    fields = {
        "id_nb": {"en": "identification number", "fr": "Identifiant"},
        "notes": {"en": "additional notes", "fr": "éléments descriptifs du contenu"},
        "vol_nb": {"en": "volume n°", "fr": "volume n°"},
        "no_vol_nb": {
            "en": "No volume number provided",
            "fr": "Pas de numéro de volume renseigné",
        },
        "cons_place": {"en": "conservation place", "fr": "lieu de conservation"},
        "work": {"en": "work", "fr": "oeuvre"},
        "place_name": {"en": "publishing place", "fr": "lieu de publication"},
        "publisher": {"en": "publisher", "fr": "éditeur"},
        "vol": {"en": "volumes", "fr": "volumes"},
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

    def to_json(self):
        return {
            "id": self.id,
            "class": self.__class__.__name__,
            "type": get_name("Series"),
            "title": self.__str__(),
            "user": self.user.__str__(),
            "is_public": self.is_public,
            "work": self.work.__str__(),
            "edition": self.edition.__str__(),
            "metadata": {
                get_name("work"): self.work.__str__(),
                get_name("dates"): format_dates(self.date_min, self.date_max),
                get_name("place_name"): self.get_edition_place(),
                get_name("publisher"): self.get_publisher(),
                get_name("cons_place"): self.place.__str__(),
                get_name("vol"): ", ".join(
                    wit.__str__() for wit in self.get_witnesses()
                )
                if self.get_witnesses()
                else "-",
            },
        }

    def get_witnesses(self):
        return self.witness_set.all()

    def get_works(self):
        return list(
            {
                content.work
                for witness in self.get_witnesses()
                for content in witness.get_contents()
                if content.work is not None
            }
        )

    def get_work_titles(self):
        works = self.get_works()
        return format_html(
            "<br>".join(
                [truncate_words(work.__str__(), TRUNCATEWORDS) for work in works]
            )
            if len(works)
            else "-"
        )

    def get_edition_place(self):
        return self.edition.place if self.edition.place else "-"

    def get_publisher(self):
        return self.edition.publisher if self.edition.publisher else "-"

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
