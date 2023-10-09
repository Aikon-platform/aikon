import os
import uuid
from glob import glob

from iiif_prezi.factory import StructuralError

from app.config.settings import APP_URL, APP_NAME
from app.webapp.models import get_wit_type, get_wit_abbr
from app.webapp.models.utils.functions import get_fieldname

import threading
from functools import partial

from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models.signals import pre_delete, pre_save, post_save
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
    IMG_ABBR,
    MAN_ABBR,
    PDF_ABBR,
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
    PDF_DIR,
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


def save_to(digit, original_filename):
    """
    Rename the file using its witness id and specific id
    The file will be uploaded to "{path}/{filename}.{ext}"
    """
    ext = original_filename.split(".")[-1]
    # images are always converted to jpg
    digit.set_ext(ext if digit.get_digit_abbr() != IMG_ABBR else "jpg")
    # NOTE here, digit_id is not yet set, digit files are renamed after with rename_digit_files()
    # TODO check how does it work for multiple images
    return f"{digit.get_relative_path()}/{uuid.uuid4()}.{ext}"


def rename_digit_files(digit):
    digit_files = (
        [digit.pdf] if digit.get_digit_abbr() == PDF_ABBR else digit.image.all()
    )
    for file in digit_files:
        if os.path.exists(digit.get_file_path()):
            log(
                f"[rename_digit_files] Already find a file with the path {digit.get_file_path()}"
            )
        os.rename(file.path, digit.get_file_path())
        file.name = digit.get_file_path(is_abs=False)


class Digitization(models.Model):
    class Meta:
        verbose_name = get_name("Digitization")
        verbose_name_plural = get_name("Digitization", True)
        app_label = "webapp"

    def __str__(self):
        return f"{self.get_digit_type()} #{self.id}: {self.witness.__str__()}"

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
        upload_to=partial(save_to),
        validators=[
            FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "tif"])
        ],
        help_text=IMG_INFO,
        blank=True,
    )
    pdf = models.FileField(
        verbose_name=PDF,
        upload_to=partial(save_to),
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
        blank=True,
    )
    manifest = models.URLField(
        verbose_name=MANIFEST,
        help_text=MANIFEST_INFO,
        validators=[validate_manifest],
        blank=True,
    )
    ext = models.CharField(verbose_name="Extension", max_length=15, default="jpg")

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
        # Returns "image" / "pdf" / "manifest" or "None"
        return str({v: k for k, v in DIGIT_ABBR.items()}.get(self.digit_type))

    def get_digit_abbr(self):
        # Returns "img" / "pdf" / "man"
        return str(self.digit_type)

    def get_annotations(self):
        return self.annotations.all()

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
        return IMG_DIR if self.digit_type == IMG_ABBR else PDF_DIR

    def get_absolute_path(self):
        return f"{MEDIA_DIR}/{self.get_relative_path()}"

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

        for filename in os.listdir(IMG_PATH):
            if filename.startswith(self.get_ref()):
                imgs.append(filename)
        return sorted(imgs)

    def save(self, *args, **kwargs):
        if not self.id:
            # TODO check to not relaunch anno if the digit didn't change
            # If the instance is being saved for the first time, save it in order to have an id
            super().save(*args, **kwargs)

        rename_digit_files(self)
        super().save(*args, **kwargs)

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
        base_url = f"{APP_URL}/{APP_NAME}/iiif/{self.get_wit_id()}/{self.id}"
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
        return "<br>".join(anno.view_btn() for anno in self.get_annotations())

    def manifest_link(self):
        from app.webapp.utils.iiif.gen_html import gen_manifest_btn

        return gen_manifest_btn(self, self.has_images())


# @receiver(pre_save, sender=Digitization)
# def digitization_pre_save(sender, instance, **kwargs):
#     # instance.ext = os.path.splitext(instance.image.name)[-1].lower()
#     # if instance.get_digit_abbr() == IMG_ABBR and instance.ext not in [".jpg", ".jpeg"]:
#     #     to_jpg(instance.image)
#     #     instance.ext = "jpg"


@receiver(post_save, sender=Digitization)
def digitization_post_save(sender, instance, created, **kwargs):
    from app.webapp.utils.iiif.annotation import send_anno_request

    if created:
        event = threading.Event()

        digit_type = instance.get_digit_abbr()
        if digit_type == PDF_ABBR:
            t = threading.Thread(
                target=pdf_to_img, args=(instance.get_file_path(is_abs=False), event)
            )
            t.start()

        elif digit_type == MAN_ABBR:
            t = threading.Thread(
                target=extract_images_from_iiif_manifest,
                args=(instance.manifest, instance.get_ref(), event),
            )
            t.start()

        elif digit_type == IMG_ABBR:
            ext = os.path.splitext(instance.image.name)[-1].lower()
            if ext not in [".jpg", ".jpeg"]:
                t = threading.Thread(
                    target=to_jpg,
                    args=(instance.image, event),
                )
                t.start()

        anno_t = threading.Thread(
            target=send_anno_request,
            args=(instance, event),
        )
        anno_t.start()


# Receive the pre_delete signal and delete the file associated with the model instance
@receiver(pre_delete, sender=Digitization)
def pre_delete_digit(sender, instance: Digitization, **kwargs):
    # Used to delete files associated to the Digitization instance
    if instance.digit_type == PDF_ABBR:
        # TODO here images associated to pdf are not deleted
        t = threading.Thread(
            target=remove_digitization,
            args=(instance, instance.pdf.name),
        )
        t.start()
    elif instance.digit_type == IMG_ABBR:
        # Pass False so ImageField doesn't save the model
        instance.image.delete(False)
    elif instance.digit_type == MAN_ABBR:
        # TODO define what to do when a manifest is deleted
        pass
    return


def remove_digitization(digit: Digitization, other_media=None):
    from app.webapp.utils.iiif.annotation import delete_annos

    for anno in digit.get_annotations():
        delete_annos(anno)

    delete_files(digit.get_imgs())
    if other_media:
        delete_files(
            other_media, MEDIA_DIR
        )  # TODO check if other media must be deleted in this dir
