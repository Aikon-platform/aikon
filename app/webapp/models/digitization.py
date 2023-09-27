import os
from glob import glob

from django.utils.safestring import mark_safe
from iiif_prezi.factory import StructuralError

from app.config.settings import APP_URL, APP_NAME
from app.webapp.models import get_wit_type, get_wit_abbr
from app.webapp.models.utils.functions import get_fieldname

import threading
from functools import partial

from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver

from app.webapp.utils.logger import log, console

from app.webapp.models.utils.constants import (
    IMG_INFO,
    MANIFEST_INFO,
    DIGIT_TYPE,
    IMG,
    PDF,
    MANIFEST,
    DIGIT_ABBR,
)
from app.webapp.utils.functions import (
    pdf_to_img,
    to_jpg,
    delete_files,
)
from app.webapp.utils.paths import (
    BASE_DIR,
    IMG_PATH,
    MEDIA_DIR,
    IMG_DIR,
    ANNO_PATH,
)

from app.webapp.utils.iiif.validation import validate_manifest
from app.webapp.utils.iiif.download import extract_images_from_iiif_manifest

from app.webapp.models.witness import Witness


def get_name(fieldname, plural=False):
    fields = {
        "source": {"en": "digitization source", "fr": "source de la numérisation"},
        "view_digit": {"en": "visualize", "fr": "visualiser"},
        "view_anno": {"en": "annotations", "fr": "annotations"},
        "is_validated": {"en": "validate annotations", "fr": "valider les annotations"},
        "is_validated_info": {
            "en": "annotations will no longer be editable",
            "fr": "les annotations ne seront plus modifiables",
        },
    }
    return get_fieldname(fieldname, fields, plural)


def rename_file(digit, original_filename):
    """
    Rename the file using its witness id and specific id
    The file will be uploaded to "{path}/{filename}.{ext}"
    """
    digit.ext = original_filename.split(".")[-1]
    new_filename = digit.get_ref()
    # TODO: create fct that do not erase the file if a image was already recorded with the same name
    # TODO check how does it work for multiple images
    return f"{digit.get_relative_path()}/{new_filename}.{digit.ext}"


def remove_digitization(digit, other_media=None):
    from app.webapp.utils.iiif.annotation import delete_annos

    delete_annos(digit)
    delete_files(digit.get_imgs())
    if other_media:
        delete_files(
            other_media, f"{BASE_DIR}/{MEDIA_DIR}"
        )  # TODO check if other media must be deleted in this dir


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

    witness = models.ForeignKey(
        Witness,
        on_delete=models.CASCADE,
        related_name="digitizations",  # to access the related contents from Witness: witness.digitizations.all()
    )
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
        blank=True,
    )
    pdf = models.FileField(
        verbose_name=PDF,
        upload_to=partial(rename_file),
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
        blank=True,
    )
    manifest = models.URLField(
        verbose_name=MANIFEST,
        help_text=MANIFEST_INFO,
        validators=[validate_manifest],
        blank=True,
    )

    def get_witness(self) -> Witness | None:
        try:
            return self.witness
        except AttributeError:
            return None

    def get_wit_type(self, abbr=False):
        if witness := self.get_witness():
            return witness.type if not abbr else get_wit_abbr(witness.type)
        return None

    def get_wit_ref(self):
        if witness := self.get_witness():
            return witness.get_ref()
        return None

    def get_wit_id(self):
        if witness := self.get_witness():
            return witness.id
        return None

    def get_digit_type(self):
        # NOTE should be returning "image" / "pdf" / "manifest"
        return str(self.digit_type)

    def get_digit_abbr(self):
        return DIGIT_ABBR[self.get_digit_type()]

    def get_annotations(self):
        return self.annotation_set.all()

    def get_ref(self):
        # digit_ref = "{wit_abbr}{wit_id}_{digit_abbr}{digit_id}"
        try:
            return f"{self.get_wit_ref()}_{self.get_digit_abbr()}{self.id}"
        except Exception:
            return None

    def set_ext(self, extension):
        self.ext = extension

    def get_relative_path(self):
        # must be relative to MEDIA_DIR
        return IMG_DIR

    def get_absolute_path(self):
        return f"{BASE_DIR}/{MEDIA_DIR}/{self.get_relative_path()}"

    def get_file_path(self, is_abs=True):
        path = self.get_absolute_path() if is_abs else self.get_relative_path()
        return f"{path}/{self.get_ref()}.{self.ext}"

    def get_anno_filenames(self):
        anno_files = []
        for anno in self.get_annotations():
            anno_files.append(anno.get_ref())
        return anno_files

    def has_annotations(self):
        # if there is at least one annotation file named after the current digitization
        if len(glob(f"{BASE_DIR}/{ANNO_PATH}/{self.get_ref()}_*.txt")):
            return True
        return False

    def has_images(self):
        # if there is at least one image file named after the current digitization
        if len(glob(f"{BASE_DIR}/{IMG_PATH}/{self.get_ref()}_*.jpg")):
            return True
        return False

    def get_imgs(self):
        imgs = []

        # pattern = re.compile(rf"{self.get_ref()}_\d{{1,4}}\.jpg", re.IGNORECASE)
        #
        # for img in os.listdir(f"{BASE_DIR}/{IMG_PATH}"):
        #     if pattern.match(img):
        #         imgs.append(img)

        for filename in os.listdir(IMG_PATH):
            if filename.startswith(self.get_ref()):
                imgs.append(filename)
        return sorted(imgs)

    def save(self, *args, **kwargs):
        from app.webapp.utils.iiif.annotation import send_anno_request

        digit_type = self.get_digit_type()
        event = threading.Event()

        if digit_type == IMG:
            ext = self.image.name.split(".")[1]
            if ext != "jpg" and ext != "jpeg":
                # TODO check how it does for multiple images
                to_jpg(self.image)
            super().save(*args, **kwargs)

        elif digit_type == PDF:
            super().save(*args, **kwargs)
            t = threading.Thread(
                target=pdf_to_img,
                args=(event, self.pdf.name),
            )
            t.start()

        elif digit_type == MANIFEST:
            super().save(*args, **kwargs)
            t = threading.Thread(
                target=extract_images_from_iiif_manifest,
                args=(self.manifest, self.get_ref(), event),
            )
            t.start()

        anno_t = threading.Thread(
            target=send_anno_request,
            args=(event, self),
        )
        anno_t.start()

    def get_metadata(self):
        # todo finish defining manifest metadata (type, id, etc)
        metadata = self.get_witness().get_metadata() if self.get_witness() else {}
        metadata["@id"] = self.get_ref()

        if manifest := self.manifest:
            metadata["Source manifest"] = str(manifest)
            metadata["Is annotated"] = self.has_annotations()

        return metadata

    def gen_manifest_url(self, only_base=False, version=None):
        # usage of version parameter to copy parameters of Annotation.gen_manifest_url()
        base_url = f"{APP_URL}/{APP_NAME}/iiif//{self.get_wit_id()}/{self.id}"
        return f"{base_url}{'' if only_base else '/manifest.json'}"

    def gen_manifest_json(self):
        from app.webapp.utils.iiif.manifest import gen_manifest_json

        error = {"error": "Unable to create a valid manifest"}
        if manifest := gen_manifest_json(self):
            try:
                return manifest.toJSON(top=True)
            except StructuralError as e:
                error["reason"] = f"{e}"
                return error
        return error

    def delete(self, using=None, keep_parents=False):
        # TODO redo that for all type of digitization
        if self.get_digit_type() == PDF:
            t = threading.Thread(
                target=remove_digitization,
                args=(self, self.pdf.name),
            )
            t.start()
        super().delete()

    def get_nb_of_pages(self):
        import PyPDF2

        with open(self.get_file_path(), "rb") as pdf_file:
            pdf_reader = PyPDF2.PdfFileReader(pdf_file)
            page_nb = pdf_reader.getNumPages()
        return page_nb

        # NOTE methods to be used inside list columns of witnesses

    def anno_btn(self):
        # To display a button in the list of witnesses to know if they were annotated or not
        return "<br>".join(anno.view_btn() for anno in self.get_annos())

    def manifest_link(self):
        from app.webapp.utils.iiif.gen_html import gen_manifest_btn

        return gen_manifest_btn(self, self.has_images())


# Receive the pre_delete signal and delete the file associated with the model instance
@receiver(pre_delete, sender=Digitization)
def pre_delete_digit(sender, digit: Digitization, **kwargs):
    # TODO use remove_digit for all type of digit
    if digit.get_digit_type() != IMG:
        return
    # Pass False so ImageField doesn't save the model
    digit.image.delete(False)
