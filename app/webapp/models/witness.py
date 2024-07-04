import json

from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils.html import format_html
from django.urls import reverse

from app.config.settings import ADDITIONAL_MODULES
from app.webapp.models.conservation_place import ConservationPlace
from app.webapp.models.edition import Edition

# from app.webapp.models.volume import Volume
from app.webapp.models.series import Series
from app.webapp.models.utils.constants import (
    VOL,
    WIT_TYPE,
    SER,
    PAGE_TYPE,
    PUBLISHED_INFO,
    AUTHOR,
    PAG_ABBR,
    PAGE,
    CONS_PLA_MSG,
    WIT_CHANGE,
    MAP_WIT_TYPE,
    MS_ABBR,
    WPR_ABBR,
    FOL_ABBR,
)
from app.webapp.models.utils.functions import get_fieldname
from app.webapp.models.work import Work
from app.webapp.utils.functions import get_icon, flatten, format_dates, get_first_img
from app.webapp.utils.logger import log


def get_name(fieldname, plural=False):
    fields = {
        "id_nb": {"en": "identification number", "fr": "cote"},
        "nb_pages": {"en": "number of pages/folios", "fr": "nombre de pages/folios"},
        "link": {
            "en": "external link (online catalog, etc.)",
            "fr": "lien externe (catalogue en ligne, etc.)",
        },
        "place_name": {"en": "creation place", "fr": "lieu de création"},
        "page_nb": {"en": "page number", "fr": "nombre de page"},
        "page_type": {"en": "pagination type", "fr": "type de pagination"},
        "page_type_info": {
            "en": "is the witness paginated, folioed, or other (scroll, etc.)?",
            "fr": "le témoin est-il paginé, folioté ou autre (rouleau, etc.)?",
        },
        "volume": {"en": VOL, "fr": VOL},
        "series": {"en": SER, "fr": SER},
        "title": {"en": "title of the volume", "fr": "titre du volume"},
        "is_public": {"en": "make it public", "fr": "rendre public"},
        "number": {"en": "volume number", "fr": "numéro de volume"},
        "number_info": {
            "en": "number useful for classifying the different volumes of an edition, but not necessarily of historical value",
            "fr": "numéro utile pour classer les différents tomes d'une édition, mais qui n'a pas nécessairement de valeur historique",
        },
    }

    return get_fieldname(fieldname, fields, plural)


class Witness(models.Model):
    class Meta:
        verbose_name = get_name("Witness")
        verbose_name_plural = get_name("Witness", True)
        # unique_together = ("id_nb", "place")
        ordering = ["-place"]
        app_label = "webapp"

    def __str__(self):
        if self.volume_title:
            vol = f", vol. {self.volume_nb}" if self.volume_nb else f" | {self.id_nb}"
            return format_html(f"{self.volume_title}{vol}")
        return format_html(
            f"{self.place.name if self.place else CONS_PLA_MSG} | {self.id_nb}"
        )

    def get_absolute_url(self):
        # return reverse("admin:webapp_witness_change", args=[self.id])
        return reverse("webapp:witness_view", args=[self.id])

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    type = models.CharField(
        verbose_name=get_name("type"), choices=WIT_TYPE, max_length=150
    )
    id_nb = models.CharField(
        verbose_name=get_name("id_nb"),
        max_length=150,
        blank=True,
        null=True,
    )
    place = models.ForeignKey(
        ConservationPlace,
        verbose_name=get_name("ConservationPlace"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    notes = models.TextField(
        verbose_name=get_name("notes"), max_length=3000, blank=True
    )
    nb_pages = models.IntegerField(
        verbose_name=get_name("nb_pages"),
        null=True,  # NOTE: this field can be automatically filled with the scan metadata
        blank=True,
    )
    page_type = models.CharField(
        verbose_name=get_name("page_type"),
        choices=PAGE_TYPE,
        max_length=150,
        default=(PAG_ABBR, PAGE.capitalize())
        # help_text=get_name('page_type_info'),
    )
    # TODO allow only user to access the record if is_public = False
    # TODO allow only the creator and super-admin to modify the record
    is_public = models.BooleanField(
        verbose_name=get_name("is_public"),
        default=False,
        help_text=f"{get_icon('triangle-exclamation')} {PUBLISHED_INFO}",
    )
    link = models.URLField(
        verbose_name=get_name("link"),
        blank=True,
    )
    slug = models.SlugField(max_length=600)  # TODO check if necessary

    # FIELDS USED ONLY FOR PRINTS
    edition = models.ForeignKey(
        Edition,
        verbose_name=get_name("Edition"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    volume_title = models.CharField(
        verbose_name=get_name("title"),
        max_length=500,
        blank=True,
        null=True,
    )
    volume_nb = models.IntegerField(
        verbose_name=get_name("number"),
        help_text=get_name("number_info"),
        blank=True,
        null=True,
    )
    series = models.ForeignKey(
        Series,
        verbose_name=get_name("series"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)

    def to_json(self):
        buttons = [
            "regions",
        ]
        if "similarity" in ADDITIONAL_MODULES:
            # TODO add other modules
            buttons += ["similarity"]

        return {
            "id": self.id,
            "class": self.__class__.__name__,
            "type": get_name("Witness"),
            "iiif": [digit.manifest_link(inline=True) for digit in self.get_digits()],
            "title": self.__str__(),
            "img": self.get_img(only_first=True),
            "user": self.user.__str__(),
            "url": self.get_absolute_url(),
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M"),
            "is_public": self.is_public,
            "metadata": {
                get_name("id_nb"): self.id_nb or "-",
                get_name("Work"): self.get_work_titles(),
                get_name("place_name"): self.get_place_names(),
                get_name("dates"): format_dates(*self.get_dates()),
                get_name("page_nb"): self.get_page(),
                get_name("Language"): self.get_lang_names(),
            },
            "buttons": buttons
            # TODO add to_json() to other models
        }

    def get_type(self):
        # NOTE should be returning "letterpress" (tpr) / "woodblock" (wpr) / "manuscript" (ms)
        return MAP_WIT_TYPE[self.type]

    def get_ref(self):
        return f"wit{self.id}"

    def get_page(self):
        return (
            f"{self.nb_pages} {'ff' if self.page_type == FOL_ABBR else 'pp'}."
            if self.nb_pages
            else "-"
        )

    def is_validated(self):
        for regions in self.get_regions():
            if not regions.is_validated:
                return False
        return True

    def change_url(self):
        change_url = reverse("admin:webapp_witness_change", args=[self.id])
        return f"<a href='{change_url}' target='_blank'>{WIT_CHANGE} #{self.id}</a>"

    def get_metadata(self):
        min_date, max_date = self.get_dates()
        metadata = {
            "Reference number": self.id_nb,
            "Work(s)": self.get_work_titles(),
            "Place(s) of production": self.get_place_names(),
            "Dates": format_dates(min_date, max_date),
            "Document type": self.get_type(),
        }
        if note := self.notes:
            metadata["Notes"] = note

        if library := self.place:
            metadata["Place of conservation"] = library.__str__()
            metadata["License"] = library.get_license()

        if self.get_persons():
            metadata = self.add_roles(metadata)

        return metadata

    def get_dates(self):
        cont_dates = [cont.get_dates() for cont in self.get_contents()]
        wit_dates = list(
            filter(
                None,
                [
                    d
                    for dates in cont_dates
                    if any(d is not None for d in dates)
                    for d in dates
                ],
            )
        )
        if len(wit_dates) == 1:
            return None, wit_dates[0]
        return (min(wit_dates), max(wit_dates)) if wit_dates else (None, None)

    def get_contents(self):
        # Django automatically creates a reverse relationship from Witness to Content
        return self.contents.all()

    def get_digits(self):
        return self.digitizations.all()

    def get_regions(self):
        regions = []
        for digit in self.get_digits():
            regions.extend(digit.get_regions())
        return regions

    def is_validated(self):
        for digit in self.get_digits():
            if digit.is_validated():
                return True
        return False

    def has_images(self):
        return any(digit.has_images() for digit in self.get_digits())

    def has_vectorization(self):
        return any(digit.has_vectorization() for digit in self.get_digits())

    def has_all_vectorization(self):
        return any(digit.has_all_vectorization() for digit in self.get_digits())

    def get_img(self, is_abs=False, only_first=False):
        # to get only one image of the witness
        for digit in self.get_digits():
            if img := digit.get_img(is_abs, only_first):
                return img

        return None

    def get_imgs(self, is_abs=False, temp=False):
        imgs = []
        for digit in self.get_digits():
            imgs.extend(digit.get_imgs(is_abs, temp))
        return imgs

    def has_regions(self):
        return any(digit.has_regions() for digit in self.get_digits())

    def get_works(self):
        return list(
            set(
                [
                    content.work
                    for content in self.get_contents()
                    if content.work is not None
                ]
            )
        )

    def get_work_titles(self):
        works = self.get_works()
        return "<br>".join([work.__str__() for work in works]) if len(works) else "-"

    def get_languages(self):
        return list(
            set(flatten([content.get_langs() for content in self.get_contents()]))
        )

    def get_lang_names(self):
        langs = self.get_languages()
        return "<br>".join([lang.__str__() for lang in langs]) if len(langs) else "-"

    def set_conservation_place(self, place: ConservationPlace):
        self.place = place

    def set_id_nb(self, id_nb):
        self.id_nb = id_nb

    def get_places(self):
        return list(
            set(
                [
                    content.place
                    for content in self.get_contents()
                    if content.place is not None
                ]
            )
        )

    def get_place_names(self):
        return "<br>".join([place.__str__() for place in self.get_places()]) or "-"

    def get_roles(self):
        return list(
            set(flatten([content.get_roles() for content in self.get_contents()]))
        )

    def get_persons(self):
        return self.contents.values_list("roles__person", flat=True).distinct()

    def get_person_names(self):
        roles = self.get_roles()
        if len(roles) == 0:
            return "-"
        return format_html("<br>".join([role.__str__() for role in roles]))

    def get_authors(self):
        return [role.person for role in self.get_roles() if role.role == AUTHOR]

    def get_author_names(self):
        # TODO add something when no author defined
        return "<br>".join([author.__str__() for author in self.get_authors()])

    def add_roles(self, metadata):
        for role in self.get_roles():
            key = role.get_role().capitalize()
            value = role.person.__str__()
            if key in metadata:
                metadata[key] += ", " + value
            else:
                metadata[key] = value
        return metadata

    def set_edition(self, edition: Edition):
        self.edition = edition

    def add_content(self, work: Work, is_complete=False):
        from app.webapp.models.content import Content

        content = Content()
        content.work = work
        content.whole_witness = is_complete
        content.witness = self
        content.save()

    def save(self, *args, **kwargs):
        self.slug = slugify(self.__str__())
        super().save(*args, **kwargs)
