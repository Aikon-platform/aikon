import os
from glob import glob

from django.utils.safestring import mark_safe
from iiif_prezi.factory import StructuralError

from app.config.settings import APP_URL, APP_NAME
from app.webapp.models import get_wit_abbr, get_wit_type
from app.webapp.models.digitization_source import DigitizationSource
from app.webapp.models.utils.functions import get_fieldname

import threading
from functools import partial

from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models.signals import pre_delete, post_save
from django.dispatch.dispatcher import receiver

from app.webapp.utils.iiif import NO_LICENSE
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
    DIG,
    SOURCE_INFO,
)
from app.webapp.utils.functions import (
    pdf_to_img,
    delete_files,
    rename_file,
    to_jpg,
    temp_to_img,
)
from app.webapp.utils.paths import (
    BASE_DIR,
    IMG_PATH,
    MEDIA_DIR,
    IMG_DIR,
    ANNO_PATH,
    PDF_DIR,
    SVG_PATH,
)

from app.webapp.utils.iiif.validation import validate_manifest
from app.webapp.utils.iiif.download import extract_images_from_iiif_manifest

from app.webapp.models.witness import Witness


ALLOWED_EXT = ["jpg", "jpeg", "png", "tif"]


def get_name(fieldname, plural=False):
    fields = {
        "view_digit": {"en": "visualize", "fr": "visualiser"},
        "view_anno": {"en": "annotations", "fr": "annotations"},
        "is_validated": {"en": "validate annotations", "fr": "valider les annotations"},
        "is_validated_info": {
            "en": "annotations will no longer be editable",
            "fr": "les annotations ne seront plus modifiables",
        },
        "is_open": {"en": "free to use", "fr": "libre d'utilisation"},
        "is_open_info": {
            "en": "are the digitized images copyright-free?",
            "fr": "les images numérisées sont-elles libres de droits ?",
        },
        "source": {"en": "digitization source", "fr": "source de la numérisation"},
    }
    return get_fieldname(fieldname, fields, plural)


def no_save(instance, original_filename):
    # NOTE here, digit_id is not yet set, digit files are renamed after with rename_files()
    return f"{instance.get_relative_path()}/to_delete.txt"


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
    # holds license information if it was contained in the source manifest
    license = models.CharField(blank=True, null=True, max_length=500)
    pdf = models.FileField(
        verbose_name=PDF,
        upload_to=PDF_DIR,
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
        blank=True,
    )
    manifest = models.URLField(
        verbose_name=MANIFEST,
        help_text=MANIFEST_INFO,
        validators=[validate_manifest],
        blank=True,
    )
    images = models.ImageField(
        verbose_name=IMG,
        upload_to=partial(no_save),
        validators=[FileExtensionValidator(allowed_extensions=ALLOWED_EXT)],
        help_text=IMG_INFO,
        blank=True,
    )
    is_open = models.BooleanField(
        verbose_name=get_name("is_open"),
        default=False,
        help_text=get_name("is_open_info"),
    )
    """source = models.CharField(
        verbose_name=get_name("source"),
        max_length=500,
        blank=True,
        null=True,
    )"""
    source = models.ForeignKey(
        DigitizationSource,
        verbose_name=get_name("source"),
        blank=True,
        null=True,
        help_text=SOURCE_INFO,
        on_delete=models.SET_NULL,
    )

    def get_witness(self):
        try:
            return self.witness
        except AttributeError:
            return None

    def get_wit_type(self, abbr=False):
        if witness := self.get_witness():
            return witness.type if abbr else get_wit_type(witness.type)
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

    def get_treatments(self):
        return self.treatments.all()

    def get_ref(self):
        # digit_ref = "{wit_abbr}{wit_id}_{digit_abbr}{digit_id}"
        try:
            return f"{self.get_wit_ref()}_{self.get_digit_abbr()}{self.id}"
        except Exception:
            return None

    def get_ext(self):
        return "jpg" if self.digit_type == IMG_ABBR else "pdf"

    def get_relative_path(self):
        # must be relative to MEDIA_DIR
        return IMG_DIR if self.digit_type == IMG_ABBR else PDF_DIR

    def get_absolute_path(self):
        return f"{MEDIA_DIR}/{self.get_relative_path()}"

    def get_file_path(self, is_abs=True, i=None, ext=None):
        path = self.get_absolute_path() if is_abs else self.get_relative_path()
        nb = f"_{i:04d}" if i else ""
        return f"{path}/{self.get_ref()}{nb}.{ext or self.get_ext()}"

    def get_anno_filenames(self):
        anno_files = []
        for anno in self.get_annotations():
            anno_files.append(anno.get_ref())
        return anno_files

    def has_annotations(self):
        # if there is at least one annotation file named after the current digitization
        if len(glob(f"{ANNO_PATH}/{self.get_ref()}_*.txt")):
            # TODO check self.get_annotations()
            return True
        return False

    def has_images(self):
        # if there is at least one image file named after the current digitization
        for i in range(1, 5):
            if os.path.exists(f"{IMG_PATH}/{self.get_ref()}_{'1'.zfill(i)}.jpg"):
                return True
        return False

    def has_vectorization(self):
        # if there is at least one SVG file named after the current digitization
        if len(glob(f"{SVG_PATH}/{self.get_ref()}_*.svg")):
            return True
        return False

    def get_imgs(self, is_abs=False, temp=False):
        imgs = []
        path = f"{IMG_PATH}/" if is_abs else ""
        for filename in os.listdir(IMG_PATH):
            if filename.startswith(
                self.get_ref() if not temp else f"temp_{self.get_wit_ref()}"
            ):
                imgs.append(f"{path}{filename}")
        return sorted(imgs)

    def get_metadata(self):
        metadata = self.get_witness().get_metadata() if self.get_witness() else {}
        metadata["@id"] = self.get_ref()

        if manifest := self.manifest:
            metadata["Source manifest"] = str(manifest)
            if license_url := self.license:
                # override license if it was previously defined
                metadata["License"] = license_url

        return metadata

    def gen_manifest_url(self, only_base=False, version=None):
        # usage of version parameter to copy parameters of Annotation.gen_manifest_url()
        base_url = f"{APP_URL}/{APP_NAME}/iiif/{self.get_ref()}"
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

    def digit_btn(self):
        from app.webapp.utils.iiif.gen_html import anno_btn

        return mark_safe(anno_btn(self, "view")) if self.has_images() else ""

    def add_source(self, source):
        # from app.webapp.models.digitization_source import DigitizationSource
        #
        # digit_source = DigitizationSource()
        # digit_source.source = source
        # digit_source.save()
        # self.source = digit_source
        self.source = source

    def view_btn(self):
        iiif_link = f"{DIG.capitalize()} #{self.id}: {self.manifest_link(inline=True)}"
        annos = self.get_annotations()
        if len(annos) == 0:
            return f"{iiif_link}<br>{self.digit_btn()}"
        return f"{iiif_link}<br>{self.anno_btn()}"

    def manifest_link(self, inline=False):
        from app.webapp.utils.iiif.gen_html import gen_manifest_btn

        return gen_manifest_btn(self, self.has_images(), inline)

    def is_valid_digit(self):
        # check if a digit type is defined but no associated file or manifest
        if self.get_digit_abbr() == PDF_ABBR and self.pdf:
            return True
        elif self.get_digit_abbr() == IMG_ABBR and self.images:
            return True
        elif self.get_digit_abbr() == MAN_ABBR and self.manifest:
            return True

        return False

    def save(self, *args, **kwargs):
        if not self.is_valid_digit():
            # if not, don't bother saving the digitization
            return

        if not self.id:
            # TODO check to not relaunch anno if the digit didn't change
            # If the instance is being saved for the first time, save it in order to have an id
            super().save(*args, **kwargs)

        if self.get_digit_abbr() == PDF_ABBR:
            rename_file(self.pdf.path, self.get_file_path())
            self.pdf.name = self.get_file_path(is_abs=False)

        elif self.get_digit_abbr() == IMG_ABBR:
            delete_files(f"{IMG_PATH}/to_delete.txt")

            i = 0
            for i, img_path in enumerate(self.get_imgs(is_abs=True, temp=True)):
                to_jpg(img_path, self.get_file_path(i=i + 1))
                print(img_path)
                delete_files(img_path)
            # TODO change to have list of image name
            self.images.name = f"{i + 1} {IMG} uploaded.jpg"

        #     delete_files(f"{IMG_PATH}/to_delete.txt")

        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        super().delete()


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

        # elif digit_type == IMG_ABBR:
        #     t = threading.Thread(
        #         target=temp_to_img, args=(instance, event)
        #     )
        #     t.start()

        elif digit_type == MAN_ABBR:

            def add_info(license_url, source):
                instance.license = license_url
                instance.add_source(source)
                if license_url != NO_LICENSE:
                    instance.is_open = True
                instance.save(update_fields=["license", "source", "is_open"])

            t = threading.Thread(
                target=extract_images_from_iiif_manifest,
                args=(instance.manifest, instance.get_ref(), event, add_info),
            )
            t.start()

        import inspect

        for frame_record in inspect.stack():
            if frame_record[3] == "get_response":
                request = frame_record[0].f_locals["request"]
                break
        else:
            request = None

        anno_t = threading.Thread(
            target=send_anno_request,
            args=(instance, event, request.user),
        )
        anno_t.start()


# Receive the pre_delete signal and delete the file associated with the model instance
@receiver(pre_delete, sender=Digitization)
def pre_delete_digit(sender, instance: Digitization, **kwargs):
    # Used to delete digit files and annotations
    other_media = instance.pdf.name if instance.digit_type == PDF_ABBR else None
    remove_digitization(instance, other_media)
    return


def remove_digitization(digit: Digitization, other_media=None):
    from app.webapp.utils.iiif.annotation import delete_annos

    for anno in digit.get_annotations():
        delete_annos(anno)

    delete_files(digit.get_imgs(is_abs=True))
    if other_media:
        delete_files(
            other_media, MEDIA_DIR
        )  # TODO check if other media must be deleted in this dir
