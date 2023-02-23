from django.contrib.auth.models import User
from django.db import models
from django.utils.text import slugify
from django.template.defaultfilters import pluralize

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

"""
Author model
"""


class Author(models.Model):
    name = models.CharField(verbose_name="Nom", max_length=200, unique=True)

    class Meta:
        verbose_name = "Auteur"
        verbose_name_plural = pluralize("Auteur")

    def __str__(self):
        return self.name


"""
Work model
"""


class Work(models.Model):
    title = models.CharField(verbose_name="Titre", max_length=600, unique=True)

    class Meta:
        verbose_name = "Titre"
        verbose_name_plural = pluralize("Titre")

    def __str__(self):
        return self.title


"""
DigitizedVersion model
"""


class DigitizedVersion(models.Model):
    source = models.CharField(max_length=150, unique=True)

    class Meta:
        verbose_name = "Source de la version numérisée"
        verbose_name_plural = "Sources des versions numérisées"

    def __str__(self):
        return self.source


"""
Printed model
"""


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
        verbose_name="Titre de l'oeuvre",
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
    description = models.TextField(verbose_name="Description de l'oeuvre")
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
        verbose_name_plural = pluralize("Imprimé")
        ordering = ["-place"]

    def __str__(self):
        return self.work.title

    def save(self, *args, **kwargs):
        self.slug = slugify(self.work.title)
        # Call the parent save method to save the model
        super().save(*args, **kwargs)


"""
Volume model
"""


class Volume(models.Model):
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
    date = models.CharField(max_length=150)
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


"""
Manuscript model
"""


class Manuscript(models.Model):
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
    # work = models.ForeignKey(
    #     Work,
    #     verbose_name="Titre de l'oeuvre",
    #     max_length=600,
    #     help_text=WORK_INFO,
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True
    # )
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
    remarks = models.TextField(verbose_name="Additional notes", blank=True)

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
        return f"{self.conservation_place} | {self.reference_number}"

    def save(self, *args, **kwargs):
        self.slug = slugify(self.reference_number)
        # Call the parent save method to save the model
        super().save(*args, **kwargs)
