import threading
from PIL import Image
from functools import partial

from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver

from vhsapp.models.constants import (
    MANIFEST,
    MS_ABBR,
    VOL_ABBR,
    IMG_INFO,
    MANIFEST_INFO,
)
from vhsapp.utils.functions import (
    rename_file,
    convert_to_jpeg,
    convert_pdf_to_image,
)
from vhsapp.utils.paths import (
    IMG_PATH,
    MS_PDF_PATH,
    VOL_PDF_PATH,
    MEDIA_PATH,
)

from vhsapp.utils.iiif import (
    parse_manifest,
    validate_manifest,
    extract_images_from_iiif_manifest,
)

from vhsapp.models.witness import Volume, Manuscript


class Digitization(models.Model):
    # TODO link this class to a unique
    # source = models.ForeignKey(
    #     Witness, verbose_name=WITNESS, on_delete=models.SET_NULL, null=True
    # )

    class Meta:
        abstract = True


#############################
#           IMG           #
#############################


class Picture(Digitization):
    class Meta:
        verbose_name = "Image file"
        verbose_name_plural = "Images files"
        abstract = True  # TODO: make this class not abstract

    def __str__(self):
        return self.image.name

    image = models.ImageField(
        verbose_name="Image",
        upload_to=partial(rename_file, path=IMG_PATH),
        validators=[
            FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "tif"])
        ],
        help_text=IMG_INFO,
    )

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
@receiver(pre_delete, sender=Picture)
def image_delete(sender, instance, **kwargs):
    # Pass false so ImageField doesn't save the model
    instance.image.delete(False)


class ImageVolume(Picture):
    volume = models.ForeignKey(Volume, on_delete=models.CASCADE)


# Receive the pre_delete signal and delete the file associated with the model instance
@receiver(pre_delete, sender=ImageVolume)
def imagevolume_delete(sender, instance, **kwargs):
    # Pass false so ImageField doesn't save the model
    instance.image.delete(False)


class ImageManuscript(Picture):
    manuscript = models.ForeignKey(Manuscript, on_delete=models.CASCADE)


# Receive the pre_delete signal and delete the file associated with the model instance
@receiver(pre_delete, sender=ImageManuscript)
def imagemanuscript_delete(sender, instance, **kwargs):
    # Pass false so ImageField doesn't save the model
    instance.image.delete(False)


#############################
#            PDF            #
#############################


class Pdf(Digitization):
    class Meta:
        verbose_name = "PDF File"
        verbose_name_plural = "PDF Files"
        abstract = True  # TODO: make this class not abstract

    def __str__(self):
        return self.pdf.name

    def save(self, *args, **kwargs):
        # Call the parent save method to save the model
        super().save(*args, **kwargs)
        # Run the PDF to image async conversion task in the background using threading
        t = threading.Thread(
            target=convert_pdf_to_image,
            args=(f"{MEDIA_PATH}/{self.pdf.name}", f"{IMG_PATH}"),
        )
        t.start()

    def delete(self, using=None, keep_parents=False):
        self.pdf.storage.delete(self.pdf.name)
        super().delete()


class PdfManuscript(Pdf):
    manuscript = models.ForeignKey(Manuscript, on_delete=models.CASCADE)
    pdf = models.FileField(
        verbose_name="PDF",
        upload_to=partial(rename_file, path=MS_PDF_PATH),
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
    )


class PdfVolume(Pdf):
    volume = models.ForeignKey(Volume, on_delete=models.CASCADE)
    pdf = models.FileField(
        verbose_name="PDF",
        upload_to=partial(rename_file, path=VOL_PDF_PATH),
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
    )


############################
#         MANIFEST         #
############################


class Manifest(Digitization):
    class Meta:
        verbose_name = "IIIF manifest"
        verbose_name_plural = "IIIF manifests"
        abstract = True  # TODO: make this class not abstract

    manifest = models.URLField(
        verbose_name=MANIFEST,
        help_text=MANIFEST_INFO,
        validators=[validate_manifest],
    )

    def __str__(self):
        return self.manifest

    # TODO: make a common save method for manifests
    # def save(self, *args, **kwargs):
    #     # Call the parent save method to save the model
    #     super().save(*args, **kwargs)
    #     # Run the async extraction of images from an IIIF manifest in the background using threading
    #     t = threading.Thread(
    #         target=extract_images_from_iiif_manifest,
    #         args=(
    #             self.manifest,
    #             f"{IMG_PATH}",
    #             f"{SRC_ABBR}{self.source.id}",
    #         ),
    #     )
    #     t.start()


class ManifestVolume(Manifest):
    volume = models.ForeignKey(Volume, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        # Call the parent save method to save the model
        super().save(*args, **kwargs)
        # Run the async extraction of images from an IIIF manifest in the background using threading
        t = threading.Thread(
            target=extract_images_from_iiif_manifest,
            args=(
                self.manifest,
                f"{VOL_ABBR}{self.volume.id}",
            ),
        )
        t.start()


class ManifestManuscript(Manifest):
    manuscript = models.ForeignKey(Manuscript, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        # Call the parent save method to save the model
        super().save(*args, **kwargs)
        # Run the async extraction of images from an IIIF manifest in the background using threading
        t = threading.Thread(
            target=extract_images_from_iiif_manifest,
            args=(
                self.manifest,
                f"{MS_ABBR}{self.manuscript.id}",
            ),
        )
        t.start()
