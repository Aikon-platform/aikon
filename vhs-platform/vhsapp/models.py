import threading
from PIL import Image
from functools import partial

from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.text import slugify
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver

from vhsapp.utils.constants import (
    CENTURY,
    MANUSCRIPT_ABBR,
    VOLUME_ABBR,
    AUTHOR_INFO,
    WORK_INFO,
    DIGITIZED_VERSION_MS_INFO,
    DIGITIZED_VERSION_VOL_INFO,
    PUBLISHED_INFO,
    MANIFEST_FINAL_INFO,
    PLACE_INFO,
    IMAGE_INFO,
    MANIFEST_INFO,
)
from vhsapp.utils.functions import (
    rename_file,
    convert_to_jpeg,
    convert_pdf_to_image,
)
from vhsapp.utils.iiif import (
    validate_gallica_manifest_url,
    validate_iiif_manifest,
    extract_images_from_iiif_manifest,
)
from vhsapp.utils.paths import (
    IMAGES_PATH,
    MANUSCRIPTS_PDFS_PATH,
    VOLUMES_PDFS_PATH,
    MEDIA_PATH,
)

"""
Author model
"""


class Author(models.Model):
    name = models.CharField(verbose_name="Nom", max_length=200, unique=True)

    class Meta:
        verbose_name = "Auteur"
        verbose_name_plural = "Auteurs"

    def __str__(self):
        return self.name


"""
Work model
"""


class Work(models.Model):
    title = models.CharField(verbose_name="Titre", max_length=600, unique=True)

    class Meta:
        verbose_name = "Titre"
        verbose_name_plural = "Titres"

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
        verbose_name_plural = "Imprimés"
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
ImageVolume model
"""


class ImageVolume(models.Model):
    volume = models.ForeignKey(Volume, on_delete=models.CASCADE)
    image = models.ImageField(
        verbose_name="Image",
        upload_to=partial(rename_file, path=IMAGES_PATH),
        validators=[
            FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "tif"])
        ],
        help_text=IMAGE_INFO,
    )

    class Meta:
        verbose_name = "Fichiers image"
        verbose_name_plural = "Fichiers image"

    def __str__(self):
        return self.image.name

    def save(self, *args, **kwargs):
        if self.image:
            img = Image.open(self.image)
            # Check if the image format is not JPEG
            if img.format != "JPEG":
                # Convert the image to JPEG format
                self.image = convert_to_jpeg(self.image)
        # Call the parent save method to save the model
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        super().delete()


# Receive the pre_delete signal and delete the file associated with the model instance
@receiver(pre_delete, sender=ImageVolume)
def imagevolume_delete(sender, instance, **kwargs):
    # Pass false so ImageField doesn't save the model
    instance.image.delete(False)


"""
PdfVolume model
"""


class PdfVolume(models.Model):
    volume = models.ForeignKey(Volume, on_delete=models.CASCADE)
    pdf = models.FileField(
        verbose_name="PDF",
        upload_to=partial(rename_file, path=VOLUMES_PDFS_PATH),
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
    )

    class Meta:
        verbose_name = "Fichier PDF"
        verbose_name_plural = "Fichiers PDF"

    def __str__(self):
        return self.pdf.name

    def save(self, *args, **kwargs):
        # Call the parent save method to save the model
        super().save(*args, **kwargs)
        # Run the PDF to image async conversion task in the background using threading
        t = threading.Thread(
            target=convert_pdf_to_image,
            args=(f"{MEDIA_PATH}{self.pdf.name}", f"{MEDIA_PATH}{IMAGES_PATH}"),
        )
        t.start()

    def delete(self, using=None, keep_parents=False):
        self.pdf.storage.delete(self.pdf.name)
        super().delete()


"""
ManifestVolume model
"""


class ManifestVolume(models.Model):
    volume = models.ForeignKey(Volume, on_delete=models.CASCADE)
    manifest = models.URLField(
        verbose_name="Manifeste",
        help_text=MANIFEST_INFO,
        validators=[validate_gallica_manifest_url, validate_iiif_manifest],
    )

    class Meta:
        verbose_name = "Manifeste"
        verbose_name_plural = "Manifestes"

    def __str__(self):
        return self.manifest

    def save(self, *args, **kwargs):
        # Call the parent save method to save the model
        super().save(*args, **kwargs)
        # Run the async extraction of images from an IIIF manifest in the background using threading
        t = threading.Thread(
            target=extract_images_from_iiif_manifest,
            args=(
                self.manifest,
                f"{MEDIA_PATH}{IMAGES_PATH}",
                f"{VOLUME_ABBR}{self.volume.id}",
            ),
        )
        t.start()


"""
Manuscript model
"""


class Manuscript(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    author = models.ForeignKey(
        Author,
        verbose_name="Auteur",
        max_length=200,
        help_text=AUTHOR_INFO,
        on_delete=models.SET_NULL,
        null=True,
    )
    work = models.ForeignKey(
        Work,
        verbose_name="Titre de l'oeuvre",
        max_length=600,
        help_text=WORK_INFO,
        on_delete=models.SET_NULL,
        null=True,
    )
    digitized_version = models.ForeignKey(
        DigitizedVersion,
        verbose_name="Source de la version numérisée",
        blank=True,
        help_text=DIGITIZED_VERSION_MS_INFO,
        on_delete=models.SET_NULL,
        null=True,
    )
    manifest_final = models.BooleanField(
        verbose_name="Valider les annotations",
        default=False,
        help_text=MANIFEST_FINAL_INFO,
    )
    slug = models.SlugField(max_length=600)
    conservation_place = models.CharField(
        verbose_name="Lieu de conservation", max_length=150
    )
    reference_number = models.CharField(verbose_name="Cote", max_length=150)
    date_century = models.CharField(
        verbose_name="Date (siècle)", choices=CENTURY, max_length=150
    )
    date_free = models.CharField(
        verbose_name="Date (champ libre)", max_length=150, blank=True
    )
    sheets = models.CharField(verbose_name="Feuillet(s)", max_length=150)
    origin_place = models.CharField(
        verbose_name="Lieu d'origine", max_length=150, blank=True
    )
    remarks = models.TextField(verbose_name="Remarques", blank=True)
    copyists = models.CharField(verbose_name="copiste(s)", max_length=150, blank=True)
    miniaturists = models.CharField(
        verbose_name="miniaturiste(s)", max_length=150, blank=True
    )
    pinakes_link = models.URLField(
        verbose_name="Lien vers Pinakes (mss grecs) ou Medium-IRHT (mss latins)",
        blank=True,
    )
    published = models.BooleanField(
        verbose_name="ATTENTION : rendre accessible publiquement",
        default=False,
        help_text=PUBLISHED_INFO,
    )
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)

    class Meta:
        verbose_name = "Manuscrit"
        verbose_name_plural = "Manuscrits"
        ordering = ["-conservation_place"]

    def __str__(self):
        return self.work.title

    def save(self, *args, **kwargs):
        self.slug = slugify(self.work.title)
        # Call the parent save method to save the model
        super().save(*args, **kwargs)


"""
ImageManuscript model
"""


class ImageManuscript(models.Model):
    manuscript = models.ForeignKey(Manuscript, on_delete=models.CASCADE)
    image = models.ImageField(
        verbose_name="Image",
        upload_to=partial(rename_file, path=IMAGES_PATH),
        validators=[
            FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "tif"])
        ],
        help_text=IMAGE_INFO,
    )

    class Meta:
        verbose_name = "Fichiers image"
        verbose_name_plural = "Fichiers image"

    def __str__(self):
        return self.image.name

    def save(self, *args, **kwargs):
        if self.image:
            img = Image.open(self.image)
            # Check if the image format is not JPEG
            if img.format != "JPEG":
                # Convert the image to JPEG format
                self.image = convert_to_jpeg(self.image)
        # Call the parent save method to save the model
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        super().delete()


# Receive the pre_delete signal and delete the file associated with the model instance
@receiver(pre_delete, sender=ImageManuscript)
def imagemanuscript_delete(sender, instance, **kwargs):
    # Pass false so ImageField doesn't save the model
    instance.image.delete(False)


"""
PdfManuscript model
"""


class PdfManuscript(models.Model):
    manuscript = models.ForeignKey(Manuscript, on_delete=models.CASCADE)
    pdf = models.FileField(
        verbose_name="PDF",
        upload_to=partial(rename_file, path=MANUSCRIPTS_PDFS_PATH),
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
    )

    class Meta:
        verbose_name = "Fichier PDF"
        verbose_name_plural = "Fichiers PDF"

    def __str__(self):
        return self.pdf.name

    def save(self, *args, **kwargs):
        # Call the parent save method to save the model
        super().save(*args, **kwargs)
        # Run the PDF to image async conversion task in the background using threading
        t = threading.Thread(
            target=convert_pdf_to_image,
            args=(f"{MEDIA_PATH}{self.pdf.name}", f"{MEDIA_PATH}{IMAGES_PATH}"),
        )
        t.start()

    def delete(self, using=None, keep_parents=False):
        self.pdf.storage.delete(self.pdf.name)
        super().delete()


"""
ManifestManuscript model
"""


class ManifestManuscript(models.Model):
    manuscript = models.ForeignKey(Manuscript, on_delete=models.CASCADE)
    manifest = models.URLField(
        verbose_name="Manifeste",
        help_text=MANIFEST_INFO,
        validators=[validate_gallica_manifest_url, validate_iiif_manifest],
    )

    class Meta:
        verbose_name = "Manifeste"
        verbose_name_plural = "Manifestes"

    def __str__(self):
        return self.manifest

    def save(self, *args, **kwargs):
        # Call the parent save method to save the model
        super().save(*args, **kwargs)
        # Run the async extraction of images from an IIIF manifest in the background using threading
        t = threading.Thread(
            target=extract_images_from_iiif_manifest,
            args=(
                self.manifest,
                f"{MEDIA_PATH}{IMAGES_PATH}",
                f"{MANUSCRIPT_ABBR}{self.manuscript.id}",
            ),
        )
        t.start()
