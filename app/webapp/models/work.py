from django.db import models
from django.urls import reverse

from app.webapp.models.language import Language
from app.webapp.models.place import Place
from app.webapp.models.person import Person
from app.webapp.models.searchable_models import AbstractSearchableModel, json_encode
from app.webapp.models.tag import Tag
from app.webapp.models.utils.constants import AUTHOR_MSG, DATE_INFO

from app.webapp.models.utils.functions import get_fieldname
from app.webapp.utils.functions import validate_dates, format_dates, flatten


def get_name(fieldname, plural=False):
    fields = {
        "place": {"en": "creation place", "fr": "lieu de création"},
        "author": {"en": "author", "fr": "auteur"},
        "dates": {"en": "dates", "fr": "dates"},
        "language": {"en": "language", "fr": "langue"},
    }
    return get_fieldname(fieldname, fields, plural)


class Work(AbstractSearchableModel):
    class Meta:
        verbose_name = get_name("Work")
        verbose_name_plural = get_name("Work", True)
        app_label = "webapp"

    def __str__(self, light=False):
        if light:
            if self.json and "title" in self.json:
                return self.json["title"]
            return self.title
        author = f"{self.author.name if self.author else AUTHOR_MSG}"
        return f"{author} | {self.title}"

    title = models.CharField(verbose_name=get_name("title"), max_length=600)
    date_min = models.IntegerField(
        verbose_name=get_name("date_min"), null=True, blank=True, help_text=DATE_INFO
    )
    date_max = models.IntegerField(
        verbose_name=get_name("date_max"), null=True, blank=True
    )
    place = models.ForeignKey(
        Place,
        verbose_name=get_name("place"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    author = models.ForeignKey(
        Person,
        verbose_name=get_name("author"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    notes = models.TextField(
        verbose_name=get_name("notes"),
        max_length=1000,
        blank=True,
        null=True,
    )
    lang = models.ManyToManyField(
        Language,
        verbose_name=get_name("Language"),
        blank=True,
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name=get_name("Tag"),
        blank=True,
    )

    def get_absolute_url(self):
        return reverse("admin:webapp_work_change", args=[self.id])
        # return reverse("webapp:work_view", args=[self.id])

    def to_json(self):
        place = self.place
        author = self.author
        return json_encode(
            {
                "id": self.id,
                "class": self.__class__.__name__,
                "type": get_name("Work"),
                # "user": self.user.__str__(),
                # "user_id": self.user.id,
                "url": self.get_absolute_url(),
                "title": self.__str__(),
                "metadata": {
                    get_name("dates"): format_dates(self.date_min, self.date_max),
                    get_name("place"): place.__str__() if place else "-",
                    get_name("author"): author.__str__() if author else "-",
                    get_name("language"): self.get_lang_names(),
                },
            }
        )

    def clean(self):
        super().clean()
        validate_dates(self.date_min, self.date_max)

    def get_witnesses(self):
        from app.webapp.models.witness import Witness

        witness_ids = self.contents.values_list("witness", flat=True).distinct()
        return Witness.objects.filter(id__in=witness_ids)

    def get_lang_names(self):
        langs = self.lang.all()
        return "<br>".join([lang.__str__() for lang in langs]) if langs else "-"
