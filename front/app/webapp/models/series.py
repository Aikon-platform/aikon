from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode

from app.config.settings import APP_LANG
from app.webapp.models.conservation_place import ConservationPlace
from app.webapp.models.edition import Edition, get_name as edition_name
from app.webapp.models.searchable_models import AbstractSearchableModel, json_encode
from app.webapp.models.tag import Tag
from app.webapp.models.utils.functions import get_fieldname
from app.webapp.models.utils.constants import PUBLISHED_INFO, DATE_INFO, NO_USER
from app.webapp.models.work import Work
from app.webapp.utils.constants import TRUNCATEWORDS
from app.webapp.utils.functions import (
    validate_dates,
    truncate_words,
    format_dates,
    get_summary,
)


def get_name(fieldname, plural=False):
    fields = {
        "id_nb": {"en": "identification number", "fr": "Identifiant"},
        "notes": {"en": "additional notes", "fr": "éléments descriptifs du contenu"},
        "vol_nb": {"en": "volume n°", "fr": "volume n°"},
        "no_vol_nb": {
            "en": "No volume number provided",
            "fr": "Pas de numéro de volume renseigné",
        },
        "shared_with": {"en": "shared with", "fr": "partagé avec"},
    }
    return get_fieldname(fieldname, fields, plural)


class Series(AbstractSearchableModel):
    class Meta:
        verbose_name = get_name("Series")
        verbose_name_plural = get_name("Series", True)
        app_label = "webapp"

    def __str__(self, light=False):
        if light and self.json and "title" in self.json:
            return self.json["title"]
        return self.edition.name

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

    shared_with = models.ManyToManyField(
        User,
        blank=True,
        related_name="shared_series",
        verbose_name=get_name("shared_with"),
    )

    def get_absolute_edit_url(self):
        return reverse("admin:webapp_series_change", args=[self.id])

    def get_absolute_view_url(self):
        query_params = {"series": f"{self.id}"}

        base_url = reverse("webapp:series_view", args=[self.id])
        query_string = urlencode(query_params)

        return f"{base_url}?{query_string}"

    def can_edit(self, user):
        if not user or not user.is_authenticated:
            return False

        return (
            user.is_superuser
            or self.user == user
            or self.shared_with.filter(pk=user.pk).exists()
            or user.groups.filter(user=self.user).exists()
        )

    def to_json(self, reindex=True, no_img=False, request_user=None):
        library = self.place
        pub_place = self.get_edition_place()
        publisher = self.get_publisher()
        work = self.work
        user = self.user
        return json_encode(
            {
                "id": self.id,
                "class": self.__class__.__name__,
                "type": get_name("Series"),
                "edit_url": self.get_absolute_edit_url(),
                "view_url": self.get_absolute_view_url(),
                "can_edit": self.can_edit(request_user),
                "title": self.__str__(),
                "user": user.__str__() if user else NO_USER,
                "user_id": user.id if user else 0,
                "is_public": self.is_public,
                "work": work.__str__() if work else "-",
                "edition": self.edition.__str__(),
                "metadata": {
                    get_name("Work"): work.__str__() if work else "-",
                    get_name("dates"): format_dates(self.date_min, self.date_max),
                    edition_name("pub_place"): pub_place.__str__()
                    if pub_place
                    else "-",
                    edition_name("publisher"): publisher.__str__()
                    if publisher
                    else "-",
                    get_name("ConservationPlace"): library.__str__()
                    if library
                    else "-",
                    get_name("Volume"): (lambda w: get_summary(w) if w else "-")(
                        self.get_witnesses()
                    ),
                },
            }
        )

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
