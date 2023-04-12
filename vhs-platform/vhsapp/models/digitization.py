import threading
from uuid import uuid4

from PIL import Image
from functools import partial

from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from pdf2image import convert_from_path

from vhsapp.utils.logger import log, console

from vhsapp.models.constants import (
    MANIFEST,
    MS_ABBR,
    VOL_ABBR,
    IMG_INFO,
    MANIFEST_INFO,
    MS,
    VOL,
    WIT,
)
from vhsapp.utils.functions import convert_to_jpeg, get_last_file
from vhsapp.utils.paths import (
    BASE_DIR,
    IMG_PATH,
    MS_PDF_PATH,
    VOL_PDF_PATH,
    MEDIA_DIR,
    IMG_DIR,
)

from vhsapp.utils.iiif import (
    parse_manifest,
    validate_manifest,
    extract_images_from_iiif_manifest,
)

from vhsapp.models.witness import Volume, Manuscript


# TODO make import work, make deletion work, make the link between witness and its digitizitaion work


class Digitization(models.Model):
    class Meta:
        abstract = True

    # TODO: make this reference the Witness class
    witness = None  # models.ForeignKey(Witness, on_delete=models.CASCADE)
    wit_type = WIT
    digit_type = "digit"

    def __init__(self, nb=None, ext=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nb = nb
        self.ext = ext

    def get_witness(self):
        return self.witness

    def get_wit_type(self):
        return self.wit_type

    def get_digit_type(self):
        return self.digit_type

    def set_ext(self, extension):
        self.ext = extension

    def get_nb(self):
        if self.get_digit_type() != "img":
            return ""
        if self.nb is None:
            self.set_nb(
                get_last_file(self.get_absolute_path(), f"{self.get_wit_ref()}_") + 1
            )
        return f"_{self.nb:04d}"

    def set_nb(self, nb):
        self.nb = nb

    def get_wit_abbr(self):
        return VOL_ABBR if self.wit_type == VOL else MS_ABBR

    def get_wit_id(self):
        if self.witness is None:
            return 0
        return self.witness.id

    def get_wit_ref(self):
        return f"{self.get_wit_abbr()}{self.get_wit_id()}"

    def get_filename(self):
        """
        Returns filename without extension
        """
        try:
            return f"{self.get_wit_ref()}{self.get_nb()}"
        except Exception:
            return None

    def get_relative_path(self):
        # must be relative to MEDIA_DIR
        return ""

    def get_absolute_path(self):
        return f"{BASE_DIR}/{MEDIA_DIR}/{self.get_relative_path()}"

    def get_file_path(self, is_abs=True):
        path = self.get_absolute_path() if is_abs else self.get_relative_path()
        return f"{path}/{self.get_filename()}.{self.ext}"


def rename_file(instance: Digitization, original_filename):
    """
    Rename the file using its witness id and specific id
    The file will be uploaded to "{path}/{filename}.{ext}"
    """
    instance.ext = original_filename.split(".")[-1]
    new_filename = instance.get_filename()
    if new_filename is None:
        # Set filename as random string
        new_filename = f"{uuid4().hex}.{instance.ext}"
    return f"{instance.get_relative_path()}/{new_filename}.{instance.ext}"


#############################
#           IMG             #
#############################


class Picture(Digitization):
    class Meta:
        verbose_name = "Image file"
        verbose_name_plural = "Images files"
        abstract = True  # TODO: make this class not abstract

    digit_type = "img"
    image = models.ImageField(
        verbose_name="Image",
        upload_to=partial(rename_file),
        validators=[
            FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "tif"])
        ],
        help_text=IMG_INFO,
    )

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

    def get_relative_path(self):
        return IMG_DIR


# Receive the pre_delete signal and delete the file associated with the model instance
@receiver(pre_delete, sender=Picture)
def imagewitness_delete(sender, instance, **kwargs):
    # Pass false so ImageField doesn't save the model
    instance.image.delete(False)


class ImageVolume(Picture):
    wit_type = VOL
    witness = models.ForeignKey(Volume, on_delete=models.CASCADE)


# Receive the pre_delete signal and delete the file associated with the model instance
@receiver(pre_delete, sender=ImageVolume)
def imagevolume_delete(sender, instance, **kwargs):
    # Pass false so ImageField doesn't save the model
    instance.image.delete(False)


class ImageManuscript(Picture):
    wit_type = MS
    witness = models.ForeignKey(
        Manuscript, on_delete=models.CASCADE, related_name="images"
    )


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

    digit_type = "pdf"
    pdf = models.FileField(
        verbose_name="PDF",
        upload_to=partial(rename_file),
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
    )

    def __str__(self):
        return self.pdf.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Run the PDF to image async conversion task in the background using threading
        t = threading.Thread(target=self.to_img())
        t.start()

    def delete(self, using=None, keep_parents=False):
        self.pdf.storage.delete(self.get_file_path(False))
        # TODO delete images extracted from the pdf
        super().delete()

    def get_page_nb(self):
        import PyPDF2

        with open(self.get_file_path(), "rb") as pdf_file:
            pdf_reader = PyPDF2.PdfFileReader(pdf_file)
            page_nb = pdf_reader.getNumPages()
        return page_nb

    def to_img(self):
        """
        Convert the PDF file to JPEG images
        """
        filename = self.get_filename()
        page_nb = self.get_page_nb()
        step = 2
        try:
            for img_nb in range(1, page_nb + 1, step):
                batch_pages = convert_from_path(
                    self.get_file_path(),
                    dpi=300,
                    first_page=img_nb,
                    last_page=min(img_nb + step - 1, page_nb),
                )
                # Iterate through all the batch pages stored above
                for page in batch_pages:
                    page.save(
                        f"{BASE_DIR}/{MEDIA_DIR}/{IMG_DIR}/{filename}_{img_nb:04d}.jpg",
                        format="JPEG",
                    )
                    # Increment the counter to update filename
                    img_nb += 1
        except Exception as e:
            log(f"Failed to convert {filename}.pdf to images:\n{e}")


class PdfManuscript(Pdf):
    witness = models.ForeignKey(Manuscript, on_delete=models.CASCADE)
    wit_type = MS

    def get_relative_path(self):
        return MS_PDF_PATH


class PdfVolume(Pdf):
    witness = models.ForeignKey(Volume, on_delete=models.CASCADE)
    wit_type = VOL

    def get_relative_path(self):
        return VOL_PDF_PATH


############################
#         MANIFEST         #
############################


class Manifest(Digitization):
    class Meta:
        verbose_name = "IIIF manifest"
        verbose_name_plural = "IIIF manifests"
        abstract = True  # TODO: make this class not abstract

    digit_type = "manifest"
    manifest = models.URLField(
        verbose_name=MANIFEST,
        help_text=MANIFEST_INFO,
        validators=[validate_manifest],
    )

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
                f"{IMG_PATH}",  # TODO here do we need an absolute path?
                f"{self.get_wit_abbr()}{self.get_wit_id()}",
            ),
        )
        t.start()


class ManifestVolume(Manifest):
    witness = models.ForeignKey(Volume, on_delete=models.CASCADE)
    wit_type = VOL


class ManifestManuscript(Manifest):
    witness = models.ForeignKey(Manuscript, on_delete=models.CASCADE)
    wit_type = MS
