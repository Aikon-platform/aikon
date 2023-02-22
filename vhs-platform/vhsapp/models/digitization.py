import threading
from PIL import Image
from functools import partial

from django.core.validators import FileExtensionValidator
from django.db import models
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
    validate_gallica_manifest_url,
    extract_images_from_iiif_manifest,
    validate_iiif_manifest,
)
from vhsapp.utils.paths import (
    IMAGES_PATH,
    MANUSCRIPTS_PDFS_PATH,
    VOLUMES_PDFS_PATH,
    MEDIA_PATH,
)

from vhsapp.models.models import Volume, Manuscript


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
