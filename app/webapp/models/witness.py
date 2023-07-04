from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

from app.webapp.models.conservation_place import ConservationPlace
from app.webapp.models.volume import Volume
from app.webapp.models.series import Series
from app.webapp.models.utils.constants import MS, VOL, WIT, WIT_TYPE, SER
from app.webapp.models.utils.functions import get_fieldname
from app.webapp.utils.functions import get_icon, flatten


def get_name(fieldname, plural=False):
    fields = {
        "id_nb": {"en": "identification number", "fr": "cote"},
        "nb_pages": {"en": "number of pages/folios", "fr": "nombre de pages/folios"},
        "link": {
            "en": "external link (online catalog, etc.)",
            "fr": "lien externe (catalogue en ligne, etc.)",
        },
        "is_paginated": {"en": "paginated?", "fr": "paginé ?"},
        "volume": {"en": VOL, "fr": "tome"},
        "series": {"en": SER, "fr": "série"},
        "title": {"en": "title of the volume", "fr": "titre du volume"},
        "is_validated": {"en": "validate annotations", "fr": "valider les annotations"},
        "is_validated_info": {
            "en": "annotations will no longer be editable",
            "fr": "les annotations ne seront plus modifiables",
        },
        "is_public": {"en": "make it public", "fr": "rendre public"},
        "is_public_info": {
            "en": "record details will be accessible to other users of the database",
            "fr": "les informations seront accessibles aux autres utilisateurs de la base",
        },
    }

    return get_fieldname(fieldname, fields, plural)


class Witness(models.Model):
    class Meta:
        verbose_name = get_name("Witness")
        verbose_name_plural = get_name("Witness", True)
        ordering = ["-place"]
        app_label = "webapp"

    def __str__(self):
        cons_place = (
            self.place.name if self.place.name else "Unknown place of conservation"
        )
        return f"{cons_place} | {self.id_nb} #{self.id}"

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    type = models.CharField(
        verbose_name=get_name("type"), choices=WIT_TYPE, max_length=150
    )
    id_nb = models.CharField(verbose_name=get_name("id_nb"), max_length=150)
    place = models.ForeignKey(
        ConservationPlace,
        verbose_name=get_name("ConservationPlace"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    # TODO volume, series
    note = models.TextField(verbose_name=get_name("note"), max_length=1000, unique=True)
    nb_pages = models.IntegerField(
        verbose_name=get_name("nb_pages"),
        null=True,  # NOTE: this field can be automatically filled with the scan metadata
        blank=True,
    )
    is_validated = models.BooleanField(
        verbose_name=get_name("is_validated"),
        default=False,
        help_text=f"{get_icon('triangle-exclamation', '#efb80b')} {get_name('is_validated_info')}",
    )
    is_public = models.BooleanField(
        verbose_name=get_name("is_public"),
        default=False,
        help_text=f"{get_icon('triangle-exclamation')} {get_name('is_public_info')}",
    )
    link = models.URLField(
        verbose_name=get_name("link"),
        blank=True,
    )
    slug = models.SlugField(max_length=600)  # TODO check if necessary

    # FIELDS USED ONLY FOR PRINTS
    title = models.CharField(verbose_name=get_name("title"), max_length=600)
    # todo finish that
    volume = models.ForeignKey(
        Volume,
        verbose_name=get_name("Volume"),
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

    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)

    def get_type(self):
        # NOTE should be returning "tpr" (letterpress) / "wpr" (woodblock) / "ms" (manuscript)
        return self.type

    def get_ref(self):
        return f"{self.get_type()}{self.id}"

    def get_metadata(self):
        metadata = {
            "Place of conservation": self.place,
            "Reference number": self.id_nb,
        }
        if note := self.note:
            metadata["Notes"] = note

        # metadata = {
        #             "Author": self.printed.author.name if self.printed.author else "No author",
        #             "Number or identifier of self": self.number_identifier,
        #             "Place": self.place,
        #             "Date": self.date,
        #             "Publishers/booksellers": self.publishers_booksellers,
        #             "Description of work": self.printed.description,
        #         }
        #         if descriptive_elements := self.printed.descriptive_elements:
        #             metadata["Descriptive elements of the content"] = descriptive_elements
        #         if illustrators := self.printed.illustrators:
        #             metadata["Illustrator(s)"] = illustrators
        #         if engravers := self.printed.engravers:
        #             metadata["Engraver(s)"] = engravers
        #         if digitized_version := self.digitized_version:
        #             metadata["Source of the digitized version"] = digitized_version.source
        #         if comment := self.comment:
        #             metadata["Comment"] = comment
        #         if other_copies := self.other_copies:
        #             metadata["Other copy(ies)"] = other_copies
        #         if manifest := self.manifestvolume_set.first():
        #             metadata["Source manifest"] = str(manifest)
        # if manifest := self.manifestmanuscript_set.first():
        #             metadata["Source manifest"] = str(manifest)
        #             metadata["Is annotated"] = has_annotations(witness, wit_abbr)

        return metadata

    def get_contents(self):
        # Django automatically creates a reverse relationship from Witness to Content
        return self.content_set.all()

    def get_roles(self):
        roles = []
        for content in self.get_contents():
            roles.append(content.get_roles())
        return flatten(roles)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.work.title)
        super().save(*args, **kwargs)
