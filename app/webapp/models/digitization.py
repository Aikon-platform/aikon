from django.db import models

from app.webapp.models.utils.functions import get_fieldname

import threading
from uuid import uuid4
from io import BytesIO
from django.core.files import File

from PIL import Image
from functools import partial

from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from pdf2image import convert_from_path

from app.webapp.utils.logger import log, console

from app.webapp.models.utils.constants import (
    MANIFEST,
    MS_ABBR,
    VOL_ABBR,
    IMG_INFO,
    MANIFEST_INFO,
    MS,
    VOL,
    WIT,
    DIGIT_TYPE,
    IMG,
    PDF,
    MANIFEST,
)
from app.webapp.utils.functions import get_last_file, get_icon
from app.webapp.utils.paths import (
    BASE_DIR,
    IMG_PATH,
    MEDIA_DIR,
    IMG_DIR,
)

from app.webapp.utils.iiif.validation import validate_manifest
from app.webapp.utils.iiif.download import extract_images_from_iiif_manifest

from app.webapp.models.witness import Witness


def get_name(fieldname, plural=False):
    fields = {
        "source": {"en": "digitization source", "fr": "source de la numérisation"},
        "app_manifest": {
            "en": "automatic annotations",
            "fr": "annotations automatiques",
        },
        "manifest_v1": {
            "en": "automatic annotations",
            "fr": "annotations automatiques",
        },
        "manifest_v2": {"en": "corrected annotations", "fr": "annotations corrigées"},
        "is_validated": {"en": "validate annotations", "fr": "valider les annotations"},
        "is_validated_info": {
            "en": "annotations will no longer be editable",
            "fr": "les annotations ne seront plus modifiables",
        },
    }
    return get_fieldname(fieldname, fields, plural)


def rename_file(digitization, original_filename):
    """
    Rename the file using its witness id and specific id
    The file will be uploaded to "{path}/{filename}.{ext}"
    """
    digitization.ext = original_filename.split(".")[-1]
    new_filename = digitization.get_filename()
    # TODO: create fct that do not erase the file if a image was already recorded with the same name
    return f"{digitization.get_relative_path()}/{new_filename}.{digitization.ext}"


# TODO make import work, make deletion work, make the link between witness and its digitizitaion work


class Digitization(models.Model):
    class Meta:
        verbose_name = get_name("Digitization")
        verbose_name_plural = get_name("Digitization", True)
        app_label = "webapp"

    def __init__(self, nb=None, ext=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nb = nb
        self.ext = ext

    def __str__(self):
        return f"{self.get_digit_type().capitalize()} #{self.id} | {self.witness.__str__()}"

    witness = models.ForeignKey(Witness, on_delete=models.CASCADE)
    digit_type = models.CharField(
        verbose_name=get_name("type"), choices=DIGIT_TYPE, max_length=150
    )

    image = models.ImageField(
        verbose_name=IMG,
        upload_to=partial(rename_file),
        validators=[
            FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "tif"])
        ],
        help_text=IMG_INFO,
    )
    pdf = models.FileField(
        verbose_name=PDF,
        upload_to=partial(rename_file),
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
    )
    manifest = models.URLField(
        verbose_name=MANIFEST,
        help_text=MANIFEST_INFO,
        validators=[validate_manifest],
    )
    is_validated = models.BooleanField(
        verbose_name=get_name("is_validated"),
        default=False,
        help_text=f"{get_icon('triangle-exclamation', '#efb80b')} {get_name('is_validated_info')}",
    )

    def get_witness(self):
        try:
            return self.witness
        except AttributeError:
            return None

    def get_wit_type(self):
        witness = self.get_witness()
        return witness.type

    def get_wit_ref(self):
        witness = self.get_witness()
        return witness.get_ref()

    def get_digit_type(self):
        # NOTE should be returning "image" / "pdf" / "manifest"
        return str(self.digit_type)

    def get_filename(self):
        """
        Returns filename without extension
        """
        # TODO: find a solution to have multiple digitizations without the same name
        # OLD return self.pdf.name.split("/")[-1].split(".")[0]
        # e.g. self.pdf.name = "pdf/filename.pdf" => filename = "filename"
        try:
            return f"{self.get_wit_ref()}_{self.id}_{self.get_nb()}"
        except Exception:
            return None

    def save(self, *args, **kwargs):
        digit_type = self.get_digit_type()

        if digit_type == IMG:
            # NOTE old version
            # if self.image:
            #     img = Image.open(self.image)
            #     if img.format != "JPEG":
            #         self.image = convert_to_jpeg(self.image)

            ext = self.image.name.split(".")[1]
            if ext != "jpg" and ext != "jpeg":
                self.to_jpg()
            super().save(*args, **kwargs)

        elif digit_type == PDF:
            super().save(*args, **kwargs)
            # Run the PDF to image async conversion task in the background using threading
            t = threading.Thread(
                target=self.to_jpg()
            )  # TODO check if a class method is working with threading
            t.start()

        elif digit_type == MANIFEST:
            super().save(*args, **kwargs)
            # Run the async extraction of images from IIIF using threading
            t = threading.Thread(
                target=extract_images_from_iiif_manifest,
                args=(self.manifest, f"{self.get_wit_ref()}"),
            )
            t.start()

    def delete(self, using=None, keep_parents=False):
        # TODO check if image_delete can be put here

        # super().delete()
        digit_type = self.get_digit_type()

        if digit_type == IMG:
            super().delete()

        elif digit_type == PDF:
            self.pdf.storage.delete(self.get_file_path(False))
            # TODO delete images extracted from the pdf
            super().delete()

    def set_ext(self, extension):
        self.ext = extension

    def get_nb(self):
        # TODO: find better solution
        if self.nb is None:
            self.set_nb(
                get_last_file(self.get_absolute_path(), f"{self.get_wit_ref()}_") + 1
            )
        return f"_{self.nb:04d}"

    def set_nb(self, nb):
        self.nb = nb

    def get_relative_path(self):
        # must be relative to MEDIA_DIR
        # TODO reorganise media folders: do we want one folder by witness or every images in the same dir
        return IMG_PATH

    def get_absolute_path(self):
        return f"{BASE_DIR}/{MEDIA_DIR}/{self.get_relative_path()}"

    def get_file_path(self, is_abs=True):
        path = self.get_absolute_path() if is_abs else self.get_relative_path()
        return f"{path}/{self.get_filename()}.{self.ext}"

    def get_nb_of_pages(self):
        import PyPDF2

        with open(self.get_file_path(), "rb") as pdf_file:
            pdf_reader = PyPDF2.PdfFileReader(pdf_file)
            page_nb = pdf_reader.getNumPages()
        return page_nb

    def to_jpg(self):
        """
        Convert images and pdf file to JPEG images
        TODO check if it works
        """
        digit_type = self.get_digit_type()

        if digit_type == IMG:
            # NOTE: might be necessary to use an external function
            img = Image.open(self.image)
            if img.mode != "RGB":
                img = img.convert("RGB")
            obj_io = BytesIO()
            img.save(obj_io, format="JPEG")
            img_jpg = File(
                obj_io, name=f"{self.get_filename()}.jpg"
            )  # TODO filename = img.name.split(".")[0]
            self.image = img_jpg

        if digit_type == PDF:
            # NOTE see for threading or task queuing
            filename = (
                self.get_wit_ref()
            )  # TODO see is not self.pdf.name (when multiple digits for one witness)
            page_nb = self.get_nb_of_pages()
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


# Receive the pre_delete signal and delete the file associated with the model instance
@receiver(pre_delete, sender=Digitization)
def image_delete(
    sender, digitization: Digitization, **kwargs
):  # NOTE does the function name have an importance?
    if digitization.get_digit_type() != IMG:
        return
    # Pass false so ImageField doesn't save the model
    # todo check if we can displace that into the delete method
    digitization.image.delete(False)
