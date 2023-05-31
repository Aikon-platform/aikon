from django.contrib.auth.models import User
from django.db import models
from django.utils.text import slugify

from vhsapp.models.constants import (
    CENTURY,
    AUTHOR_INFO,
    WORK_INFO,
    DIGITIZED_VERSION_MS_INFO,
    DIGITIZED_VERSION_VOL_INFO,
    PUBLISHED_INFO,
    MANIFEST_FINAL_INFO,
    PLACE_INFO,
)

from vhsapp.models.models import Work, Author, DigitizedVersion
from vhsapp.models.constants import (
    MS,
    VOL,
    WIT,
)


# TODO factorize Volume and Printed attributes/methods in this class
class Witness(models.Model):
    class Meta:
        abstract = True
        verbose_name = WIT
        verbose_name_plural = "Witnesses"

    type = WIT


class Printed(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    author = models.ForeignKey(
        Author,
        verbose_name="Auteurs et/ou Éditeurs scientifiques",
        max_length=200,
        help_text=AUTHOR_INFO,
        on_delete=models.SET_NULL,
        null=True,
    )
    work = models.ForeignKey(
        Work,
        verbose_name="Titre de l'œuvre",
        max_length=600,
        on_delete=models.SET_NULL,
        null=True,
    )
    slug = models.SlugField(max_length=600)
    place = models.CharField(verbose_name="Lieu", max_length=150)
    date = models.CharField(max_length=150)
    publishers_booksellers = models.CharField(
        verbose_name="Éditeurs/libraires", max_length=150
    )
    description = models.TextField(verbose_name="Description de l'œuvre")
    descriptive_elements = models.TextField(
        verbose_name="Éléments descriptifs du contenu", blank=True
    )
    illustrators = models.CharField(
        verbose_name="Dessinateur(s)", max_length=150, blank=True
    )
    engravers = models.CharField(verbose_name="Graveur(s)", max_length=150, blank=True)
    published = models.BooleanField(
        verbose_name="ATTENTION : rendre accessible publiquement",
        default=False,
        help_text=PUBLISHED_INFO,
    )
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)

    class Meta:
        verbose_name = "Imprimé"
        verbose_name_plural = "Imprimés"
        ordering = ["-place"]

    def __str__(self):
        return self.work.title

    def save(self, *args, **kwargs):
        self.slug = slugify(self.work.title)
        # Call the parent save method to save the model
        super().save(*args, **kwargs)


class Volume(models.Model):
    type = VOL
    printed = models.ForeignKey(
        Printed, verbose_name="Imprimé", on_delete=models.CASCADE
    )
    digitized_version = models.ForeignKey(
        DigitizedVersion,
        verbose_name="Source de la version numérisée",
        blank=True,
        help_text=DIGITIZED_VERSION_VOL_INFO,
        on_delete=models.SET_NULL,
        null=True,
    )
    manifest_final = models.BooleanField(
        verbose_name="Valider les annotations",
        default=False,
        help_text=MANIFEST_FINAL_INFO,
    )
    title = models.CharField(verbose_name="Titre du volume", max_length=600)
    slug = models.SlugField(max_length=600)
    number_identifier = models.CharField(
        verbose_name="Numéro ou élément d'identification du volume", max_length=150
    )
    place = models.CharField(verbose_name="Lieu", max_length=150, help_text=PLACE_INFO)
    date_min = models.IntegerField(verbose_name="Date min", null=True, blank=True)
    date_max = models.IntegerField(verbose_name="Date max", null=True, blank=True)
    publishers_booksellers = models.CharField(
        verbose_name="Éditeurs/libraires", max_length=150
    )
    comment = models.TextField(verbose_name="Commentaire éventuel", blank=True)
    other_copies = models.TextField(verbose_name="Autre(s) exemplaire(s)", blank=True)
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)

    class Meta:
        verbose_name = "Volume"
        verbose_name_plural = "Volumes"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        # Call the parent save method to save the model
        super().save(*args, **kwargs)

    def get_metadata(self):
        metadata = {
            "Author": self.printed.author.name if self.printed.author else "No author",
            "Number or identifier of self": self.number_identifier,
            "Place": self.place,
            "Date": self.date,
            "Publishers/booksellers": self.publishers_booksellers,
            "Description of work": self.printed.description,
        }
        if descriptive_elements := self.printed.descriptive_elements:
            metadata["Descriptive elements of the content"] = descriptive_elements
        if illustrators := self.printed.illustrators:
            metadata["Illustrator(s)"] = illustrators
        if engravers := self.printed.engravers:
            metadata["Engraver(s)"] = engravers
        if digitized_version := self.digitized_version:
            metadata["Source of the digitized version"] = digitized_version.source
        if comment := self.comment:
            metadata["Comment"] = comment
        if other_copies := self.other_copies:
            metadata["Other copy(ies)"] = other_copies

        return metadata


class Manuscript(models.Model):
    type = MS
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    author = models.ForeignKey(
        Author,
        verbose_name="Author",
        max_length=200,
        help_text=AUTHOR_INFO,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    work = models.ForeignKey(
        Work,
        verbose_name="Titre de l'œuvre",
        max_length=600,
        help_text=WORK_INFO,
        on_delete=models.SET_NULL,
        null=True,
    )
    digitized_version = models.ForeignKey(
        DigitizedVersion,
        verbose_name="Source of the digitized version",
        blank=True,
        help_text=DIGITIZED_VERSION_MS_INFO,
        on_delete=models.SET_NULL,
        null=True,
    )
    manifest_final = models.BooleanField(
        verbose_name="Validate annotations",
        default=False,
        help_text=MANIFEST_FINAL_INFO,
    )
    slug = models.SlugField(max_length=600)
    conservation_place = models.CharField(
        verbose_name="Conservation place", max_length=150
    )
    reference_number = models.CharField(verbose_name="Shelfmark", max_length=150)
    # date_century = models.CharField(verbose_name="Century", choices=CENTURY, max_length=150)
    date_free = models.CharField(verbose_name="Date", max_length=150, blank=True)
    sheets = models.CharField(verbose_name="Number of folios/pages", max_length=150)
    origin_place = models.CharField(
        verbose_name="Place of production", max_length=150, blank=True
    )
    copyists = models.CharField(verbose_name="Copyist(s)", max_length=150, blank=True)
    miniaturists = models.CharField(
        verbose_name="Illuminator(s)", max_length=150, blank=True
    )
    pinakes_link = models.URLField(
        verbose_name="External link",
        blank=True,
    )
    remarks = models.TextField(verbose_name="Additional note", blank=True)

    published = models.BooleanField(
        verbose_name="Make public",
        default=False,
        help_text=PUBLISHED_INFO,
    )
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)

    class Meta:
        verbose_name = "Manuscript"
        verbose_name_plural = "Manuscripts"
        ordering = ["-conservation_place"]

    def __str__(self):
        cons_place = (
            self.conservation_place
            if self.conservation_place
            else "Unknown place of conservation"
        )
        ref = self.reference_number if self.reference_number else "No reference number"
        return f"{cons_place} | {ref}"

    def save(self, *args, **kwargs):
        self.slug = slugify(self.reference_number)
        # Call the parent save method to save the model
        super().save(*args, **kwargs)

    # def delete(self, *args, **kwargs):
    #     # delete related images
    #     self.images.all().delete()  # MARKER: supposedly accessible because of related_names in Digitization
    #     super().delete(*args, **kwargs)

    def get_metadata(self):
        metadata = {
            "Author": self.author.name if self.author else "No author",
            "Place of conservation": self.conservation_place,
            "Reference number": self.reference_number,
            # "Date (century)": self.date_century,
            "Sheet(s)": self.sheets,
        }
        if date_free := self.date_free:
            metadata["Date"] = date_free
        if origin_place := self.origin_place:
            metadata["Place of origin"] = origin_place
        if remarks := self.remarks:
            metadata["Remarks"] = remarks
        if copyists := self.copyists:
            metadata["Copyist(s)"] = copyists
        if miniaturists := self.miniaturists:
            metadata["Miniaturist(s)"] = miniaturists
        if digitized_version := self.digitized_version:
            metadata["Source of the digitized version"] = digitized_version.source
        if pinakes_link := self.pinakes_link:
            metadata["External link"] = pinakes_link

        return metadata


# from django.contrib.auth.models import User
# from django.db import models
# from django.utils.text import slugify
#
# from vhsapp.models.constants import (
#     CENTURY,
#     AUTHOR_INFO,
#     WORK_INFO,
#     DIGITIZED_VERSION_MS_INFO,
#     DIGITIZED_VERSION_VOL_INFO,
#     PUBLISHED_INFO,
#     MANIFEST_FINAL_INFO,
#     PLACE_INFO,
# )
#
# from vhsapp.models.models import Work, Author, DigitizedVersion
#
#
# class Printed(models.Model):
#     user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
#     author = models.ForeignKey(
#         Author,
#         verbose_name="Auteurs et/ou Éditeurs scientifiques",
#         max_length=200,
#         help_text=AUTHOR_INFO,
#         on_delete=models.SET_NULL,
#         null=True,
#     )
#     work = models.ForeignKey(
#         Work,
#         verbose_name="Titre de l'oeuvre",
#         max_length=600,
#         on_delete=models.SET_NULL,
#         null=True,
#     )
#     slug = models.SlugField(max_length=600)
#     place = models.CharField(verbose_name="Lieu", max_length=150)
#     date = models.CharField(max_length=150)
#     publishers_booksellers = models.CharField(
#         verbose_name="Éditeurs/libraires", max_length=150
#     )
#     description = models.TextField(verbose_name="Description de l'oeuvre")
#     descriptive_elements = models.TextField(
#         verbose_name="Éléments descriptifs du contenu", blank=True
#     )
#     illustrators = models.CharField(
#         verbose_name="Dessinateur(s)", max_length=150, blank=True
#     )
#     engravers = models.CharField(verbose_name="Graveur(s)", max_length=150, blank=True)
#     published = models.BooleanField(
#         verbose_name="ATTENTION : rendre accessible publiquement",
#         default=False,
#         help_text=PUBLISHED_INFO,
#     )
#     created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
#     updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)
#
#     class Meta:
#         verbose_name = "Imprimé"
#         verbose_name_plural = "Imprimés"
#         ordering = ["-place"]
#
#     def __str__(self):
#         return self.work.title
#
#     def save(self, *args, **kwargs):
#         self.slug = slugify(self.work.title)
#         # Call the parent save method to save the model
#         super().save(*args, **kwargs)
#
#
# class Volume(models.Model):
#     printed = models.ForeignKey(
#         Printed, verbose_name="Imprimé", on_delete=models.CASCADE
#     )
#     digitized_version = models.ForeignKey(
#         DigitizedVersion,
#         verbose_name="Source de la version numérisée",
#         blank=True,
#         help_text=DIGITIZED_VERSION_VOL_INFO,
#         on_delete=models.SET_NULL,
#         null=True,
#     )
#     manifest_final = models.BooleanField(
#         verbose_name="Valider les annotations",
#         default=False,
#         help_text=MANIFEST_FINAL_INFO,
#     )
#     title = models.CharField(verbose_name="Titre du volume", max_length=600)
#     slug = models.SlugField(max_length=600)
#     number_identifier = models.CharField(
#         verbose_name="Numéro ou élément d'identification du volume", max_length=150
#     )
#     place = models.CharField(verbose_name="Lieu", max_length=150, help_text=PLACE_INFO)
#     date = models.CharField(max_length=150)
#     publishers_booksellers = models.CharField(
#         verbose_name="Éditeurs/libraires", max_length=150
#     )
#     comment = models.TextField(verbose_name="Commentaire éventuel", blank=True)
#     other_copies = models.TextField(verbose_name="Autre(s) exemplaire(s)", blank=True)
#     created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
#     updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)
#
#     class Meta:
#         verbose_name = "Volume"
#         verbose_name_plural = "Volumes"
#
#     def __str__(self):
#         return self.title
#
#     def save(self, *args, **kwargs):
#         self.slug = slugify(self.title)
#         # Call the parent save method to save the model
#         super().save(*args, **kwargs)
#
#     def get_metadata(self):
#         metadata = {
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
#
#         return metadata
#
#
# class Manuscript(models.Model):
#     user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
#     author = models.ForeignKey(
#         Author,
#         verbose_name="Author",
#         max_length=200,
#         help_text=AUTHOR_INFO,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#     )
#     # work = models.ForeignKey(
#     #     Work,
#     #     verbose_name="Titre de l'oeuvre",
#     #     max_length=600,
#     #     help_text=WORK_INFO,
#     #     on_delete=models.SET_NULL,
#     #     null=True,
#     #     blank=True
#     # )
#     digitized_version = models.ForeignKey(
#         DigitizedVersion,
#         verbose_name="Source of the digitized version",
#         blank=True,
#         help_text=DIGITIZED_VERSION_MS_INFO,
#         on_delete=models.SET_NULL,
#         null=True,
#     )
#     manifest_final = models.BooleanField(
#         verbose_name="Validate annotations",
#         default=False,
#         help_text=MANIFEST_FINAL_INFO,
#     )
#     slug = models.SlugField(max_length=600)
#     conservation_place = models.CharField(
#         verbose_name="Conservation place", max_length=150
#     )
#     reference_number = models.CharField(verbose_name="Shelfmark", max_length=150)
#     # date_century = models.CharField(
#     #     verbose_name="Century", choices=CENTURY, blank=True, max_length=150
#     # )
#     date_free = models.CharField(verbose_name="Date", max_length=150, blank=True)
#     sheets = models.CharField(verbose_name="Number of folios/pages", max_length=150)
#     origin_place = models.CharField(
#         verbose_name="Place of production", max_length=150, blank=True
#     )
#     copyists = models.CharField(verbose_name="Copyist(s)", max_length=150, blank=True)
#     miniaturists = models.CharField(
#         verbose_name="Illuminator(s)", max_length=150, blank=True
#     )
#     pinakes_link = models.URLField(
#         verbose_name="External link",
#         blank=True,
#     )
#     remarks = models.TextField(verbose_name="Additional note", blank=True)
#
#     published = models.BooleanField(
#         verbose_name="Make public",
#         default=False,
#         help_text=PUBLISHED_INFO,
#     )
#     created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
#     updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)
#
#     class Meta:
#         verbose_name = "Manuscript"
#         verbose_name_plural = "Manuscripts"
#         ordering = ["-conservation_place"]
#
#     def __str__(self):
#         cons_place = (
#             self.conservation_place
#             if self.conservation_place
#             else "Unknown place of conservation"
#         )
#         ref = self.reference_number if self.reference_number else "No reference number"
#         return f"{cons_place} | {ref}"
#
#     def save(self, *args, **kwargs):
#         self.slug = slugify(self.reference_number)
#         # Call the parent save method to save the model
#         super().save(*args, **kwargs)
#
#     def get_metadata(self):
#         metadata = {
#             "Author": self.author.name if self.author else "No author",
#             "Place of conservation": self.conservation_place,
#             "Reference number": self.reference_number,
#             # "Date (century)": self.date_century,
#             "Sheet(s)": self.sheets,
#         }
#         if date_free := self.date_free:
#             metadata["Date"] = date_free
#         if origin_place := self.origin_place:
#             metadata["Place of origin"] = origin_place
#         if remarks := self.remarks:
#             metadata["Remarks"] = remarks
#         if copyists := self.copyists:
#             metadata["Copyist(s)"] = copyists
#         if miniaturists := self.miniaturists:
#             metadata["Miniaturist(s)"] = miniaturists
#         if digitized_version := self.digitized_version:
#             metadata["Source of the digitized version"] = digitized_version.source
#         if pinakes_link := self.pinakes_link:
#             metadata["External link"] = pinakes_link
#         if manifest := self.manifestmanuscript_set.first():
#             metadata["Source manifest"] = str(manifest)
#
#         return metadata
