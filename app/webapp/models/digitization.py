import os
from glob import glob

from django.utils.safestring import mark_safe
from iiif_prezi.factory import StructuralError

from app.config.settings import APP_URL, APP_NAME
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
    MAN,
    DIGIT_ABBR,
    IMG_ABBR,
    MAN_ABBR,
    PDF_ABBR,
    DIG,
    SOURCE_INFO,
    MANIFEST_V2,
)
from app.webapp.utils.functions import (
    delete_files,
    rename_file,
    get_nb_of_files,
    get_first_img,
    get_files_with_prefix,
)
from app.webapp.utils.paths import (
    IMG_PATH,
    MEDIA_DIR,
    IMG_DIR,
    REGIONS_PATH,
    PDF_DIR,
)
from app.webapp.tasks import (
    convert_pdf_to_img,
    convert_temp_to_img,
    extract_images_from_iiif_manifest,
)

from app.webapp.utils.iiif.validation import validate_manifest

from app.webapp.models.witness import Witness


ALLOWED_EXT = ["jpg", "jpeg", "png", "tif"]


def get_name(fieldname, plural=False):
    fields = {
        "view_digit": {"en": "visualize", "fr": "visualiser"},
        "view_regions": {"en": "regions", "fr": "régions"},
        "is_validated": {"en": "validate regions", "fr": "valider les régions"},
        "is_validated_info": {
            "en": "regions will no longer be editable",
            "fr": "les régions ne seront plus modifiables",
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

    def __str__(self, light=False):
        if light:
            return f"{self.get_digit_type()} #{self.id}"
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
        verbose_name=MAN,
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
        if witness := self.witness:
            return witness
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

    def get_regions(self):
        return self.regions.all()

    # def get_treatments(self):
    #     return self.treatments.all()

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

    def get_regions_filenames(self):
        regions_files = []
        for regions in self.get_regions():
            regions_files.append(regions.get_ref())
        return regions_files

    def has_regions(self):
        # if there is at least one regions file named after the current digitization
        if len(glob(f"{REGIONS_PATH}/{self.get_ref()}_*.txt")):
            # TODO check self.get_regions()
            return True
        return False

    def has_images(self):
        # if there is at least one image file named after the current digitization
        # NOTE: might result in returning None even though there are images (but not the first one)
        return bool(get_first_img(self.get_ref()))

    def has_digit(self):
        # if there is either a pdf/manifest/img associated with the digitization
        return bool(self.pdf or self.manifest or self.images)

    def img_nb(self):
        # get the number of images for a digitization
        return get_nb_of_files(IMG_PATH, self.get_ref()) or 0

    def img_zeros(self):
        # get the number of digits for the images of this digitization (to know number of trailing zeros)
        first_img = get_first_img(self.get_ref())
        if not first_img:
            return 0
        return len(get_first_img(self.get_ref()).split("_")[-1].split(".")[0])

    def has_vectorization(self):
        # TODO voir comment modulariser ?
        from app.vectorization.const import SVG_PATH

        # if there is at least one SVG file named after the current digitization
        if len(glob(f"{SVG_PATH}/{self.get_ref()}_*.svg")):
            return True
        return False

    ####### WORK IN PROGRESS

    def count_annotations(self):
        from app.webapp.utils.iiif.annotation import total_annotations

        count = 0
        for regions in self.get_regions():
            count += total_annotations(regions)

        return count

    def has_all_vectorizations(self):
        from app.vectorization.const import SVG_PATH

        # if there is as much svg files as there are regions in the current digitization
        if len(glob(f"{SVG_PATH}/{self.get_ref()}_*.svg")) == self.count_annotations():
            return True
        return False

    def check_vectorizations(self):
        # TODO improve
        from app.vectorization.const import SVG_PATH
        from app.webapp.utils.iiif.annotation import create_list_annotations

        # Liste de tous les fichiers SVG correspondants
        svg_files_paths = glob(f"{SVG_PATH}/{self.get_ref()}_*.svg")

        # Vérifie que svg_files_paths est bien une liste
        print(f"svg_files_paths : {svg_files_paths}")

        # Extraire les noms de fichiers à partir des chemins sans l'extension ".svg"
        svg_files_names = [
            os.path.basename(file_path).replace(".svg", "")
            for file_path in svg_files_paths
        ]

        # Récupérer la liste des annotations des régions
        regions_list = []
        for regions in self.get_regions():
            regions_list.extend(create_list_annotations(regions))

        # Comparer les noms de fichiers SVG et les régions
        print(sorted(svg_files_names))
        print(sorted(regions_list))
        return (
            bool(svg_files_names)
            and bool(regions_list)
            and sorted(svg_files_names) == sorted(regions_list)
        )

    ####### WORK IN PROGRESS

    def get_img(self, is_abs=False, only_first=False):
        if only_first:
            return get_first_img(self.get_ref())
        return self.get_imgs(is_abs, only_one=True)

    def get_imgs(self, is_abs=False, temp=False, only_one=False):
        prefix = f"{self.get_ref()}_" if not temp else f"temp_{self.get_wit_ref()}"
        path = f"{IMG_PATH}/" if is_abs else ""
        return sorted(get_files_with_prefix(IMG_PATH, prefix, path, only_one))

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
        # usage of version parameter to copy parameters of Regions.gen_manifest_url()
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

    def regions_btn(self):
        # To display a button in the list of witnesses to know if regions were extracted or not
        return "<br>".join(regions.view_btn() for regions in self.get_regions())

    def digit_btn(self):
        from app.webapp.utils.iiif.gen_html import regions_btn

        return mark_safe(regions_btn(self, "view")) if self.has_images() else ""

    # def add_source(self, source):
    #     # from app.webapp.models.digitization_source import DigitizationSource
    #     #
    #     # digit_source = DigitizationSource()
    #     # digit_source.source = source
    #     # digit_source.save()
    #     # self.source = digit_source
    #     self.source = source

    def view_btn(self):
        iiif_link = f"{DIG.capitalize()} #{self.id}: {self.manifest_link(inline=True)}"
        regions = self.get_regions()
        if len(regions) == 0:
            return f"{iiif_link}<br>{self.digit_btn()}"
        return f"{iiif_link}<br>{self.regions_btn()}"
        # return f"{DIG.capitalize()} #{self.id}: {self.manifest_link(inline=True)}"

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
            # TODO check to not relaunch regions if the digit didn't change
            # If the instance is being saved for the first time, save it in order to have an id
            super().save(*args, **kwargs)

        if self.get_digit_abbr() == PDF_ABBR:
            rename_file(self.pdf.path, self.get_file_path())
            self.pdf.name = self.get_file_path(is_abs=False)

        elif self.get_digit_abbr() == IMG_ABBR:
            self.images.name = f"{IMG} uploaded.jpg"

        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        super().delete()

    def add_info(self, license_url, source):
        self.license = license_url
        # self.add_source(source)
        if license_url != NO_LICENSE:
            self.is_open = True
        self.save(update_fields=["license", "source", "is_open"])


@receiver(post_save, sender=Digitization)
def digitization_post_save(sender, instance, created, **kwargs):
    if created:
        digit_type = instance.get_digit_abbr()
        if digit_type == PDF_ABBR:
            convert_pdf_to_img.delay(instance.get_file_path(is_abs=False))

        elif digit_type == IMG_ABBR:
            convert_temp_to_img.delay(instance)

        elif digit_type == MAN_ABBR:
            extract_images_from_iiif_manifest.delay(
                instance.manifest, instance.get_ref(), instance
            )


# Receive the pre_delete signal and delete the file associated with the model instance
@receiver(pre_delete, sender=Digitization)
def pre_delete_digit(sender, instance: Digitization, **kwargs):
    # Used to delete digit files and regions
    other_media = instance.pdf.name if instance.digit_type == PDF_ABBR else None
    remove_digitization(instance, other_media)
    return


def remove_digitization(digit: Digitization, other_media=None):
    from app.webapp.utils.iiif.annotation import delete_regions

    for regions in digit.get_regions():
        delete_regions(regions)

    delete_files(digit.get_imgs(is_abs=True))
    if other_media:
        delete_files(other_media, MEDIA_DIR)
