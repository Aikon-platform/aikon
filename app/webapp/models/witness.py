from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils.html import format_html
from django.urls import reverse

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
)
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
        "page_type": {"en": "pagination type", "fr": "type de pagination"},
        "page_type_info": {
            "en": "is the witness paginated, folioed, or other (scroll, etc.)?",
            "fr": "le témoin est-il paginé, folioté ou autre (rouleau, etc.)?",
        },
        "volume": {"en": VOL, "fr": VOL},
        "series": {"en": SER, "fr": SER},
        "title": {"en": "title of the volume", "fr": "titre du volume"},
        "is_public": {"en": "make it public", "fr": "rendre public"},
        "number": {"en": "volume number", "fr": "numéro de tome"},
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
        unique_together = ("id_nb", "place")
        ordering = ["-place"]
        app_label = "webapp"

    def __str__(self):
        cons_place = self.place.name if self.place else CONS_PLA_MSG
        return format_html(f"{cons_place} | {self.id_nb}")

    def get_absolute_url(self):
        return reverse("admin:webapp_witness_change", args=[self.id])

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
    notes = models.TextField(
        verbose_name=get_name("notes"), max_length=1000, blank=True
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

    def change_url(self):
        change_url = reverse("admin:webapp_witness_change", args=[self.id])
        return f"<a href='{change_url}' target='_blank'>{WIT_CHANGE} #{self.id}</a>"

    def get_metadata(self):
        # todo finish defining manifest metadata (type, id, etc)

        metadata = {
            "Reference number": self.id_nb,
            "Work(s)": self.get_work_titles(),
            "Place(s) of production": self.get_place_names(),
        }
        if note := self.notes:
            metadata["Notes"] = note

        if library := self.place:
            metadata["Place of conservation"] = library.__str__()
            metadata["Licence"] = library.get_licence()

        if self.get_persons():
            metadata = self.add_roles(metadata)

        # metadata = {
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

        return metadata

    def get_dates(self):
        cont_dates = [cont.get_dates() for cont in self.get_contents()]
        wit_dates = [
            d
            for dates in cont_dates
            if any(d is not None for d in dates)
            for d in dates
        ]
        return (min(wit_dates), max(wit_dates)) if wit_dates else (None, None)

    def get_contents(self):
        # Django automatically creates a reverse relationship from Witness to Content
        return self.contents.all()

    def get_digits(self):
        return self.digitizations.all()

    def get_annotations(self):
        annos = []
        for digit in self.get_digits():
            annos.extend(digit.get_annotations())
        return annos

    def is_validated(self):
        for digit in self.get_digits():
            if digit.is_validated():
                return True
        return False

    def has_images(self):
        return any(digit.has_images() for digit in self.get_digits())

    def get_imgs(self, is_abs=False, temp=False):
        imgs = []
        for digit in self.get_digits():
            imgs.extend(digit.get_imgs(is_abs, temp))
        return imgs

    def has_annotations(self):
        return any(digit.has_annotations() for digit in self.get_digits())

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
        return flatten([content.get_roles() for content in self.get_contents()])

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

    def save(self, *args, **kwargs):
        self.slug = slugify(self.__str__())
        super().save(*args, **kwargs)
