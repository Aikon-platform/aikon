import os
from glob import glob
from functools import partial
from typing import Optional, List

from iiif_prezi.factory import StructuralError

from django.utils.safestring import mark_safe
from django.core.validators import FileExtensionValidator
from django.db import models, transaction
from django.db.models.signals import pre_delete, post_save
from django.dispatch.dispatcher import receiver

from app.config.settings import APP_URL, APP_NAME
from app.webapp.models.digitization_source import DigitizationSource
from app.webapp.models.searchable_models import AbstractSearchableModel
from app.webapp.models.utils.functions import get_fieldname
from app.webapp.utils.iiif.validation import validate_manifest
from app.webapp.models.witness import Witness
from app.webapp.utils.iiif import NO_LICENSE
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
    MEDIA_PATH,
    IMG_DIR,
    REGIONS_PATH,
    PDF_DIR,
)
from webapp.utils.paths import TMP_PATH

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
    # NOTE here, digit_id is not yet set, digit files are renamed afterwards
    #  inside temp_to_img() with digit.get_file_path()
    return f"{instance.get_relative_path()}/to_delete.txt"


class Digitization(AbstractSearchableModel):
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
        return f"{MEDIA_PATH}/{self.get_relative_path()}"

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
        if len(glob(f"{REGIONS_PATH}/{self.get_ref()}_*")):
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

    def img_nb(self, check_in_dir=False):
        # get the number of images for a digitization
        if not check_in_dir:
            if img_nb := self.get_key_value("img_nb"):
                return img_nb

        return get_nb_of_files(IMG_PATH, self.get_ref()) or 0

    def img_zeros(self, first_img_filename=None, check_in_dir=False):
        # get the number of digits for the images of this digitization (to know number of trailing zeros)
        if not first_img_filename:
            if not check_in_dir:
                if zero_nb := self.get_key_value("zeros"):
                    return zero_nb
            first_img_filename = get_first_img(self.get_ref())
        if not first_img_filename:
            return 0
        return len(first_img_filename.split("_")[-1].split(".")[0])

    def has_vectorization(self):
        # TODO check how to handle this with additional modules
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

    def svg_paths(self):
        # TODO save SVG in different folders
        from app.vectorization.const import SVG_PATH

        return glob(f"{SVG_PATH}/{self.get_ref()}_*.svg")

    def has_all_vectorizations(self):
        # if there are as many svg files as there are regions in the current digitization
        if len(self.svg_paths()) == self.count_annotations():
            return True
        return False

    def is_vectorized(self):
        """
        :return: True if all regions have vectorizations, False otherwise
        """
        return all(region.is_vectorized() for region in self.get_regions())

    ####### WORK IN PROGRESS

    def get_img(self, is_abs=False, only_first=False):
        if only_first:
            return get_first_img(self.get_ref())
        return self.get_imgs(is_abs, only_one=True)

    def get_imgs(self, is_abs=False, temp=False, only_one=False, check_in_dir=False):
        if not check_in_dir and not temp:
            if imgs := self.get_key_value("imgs"):
                return imgs[0] if only_one else imgs

        prefix = f"{self.get_ref()}_" if not temp else f"temp_{self.get_wit_ref()}"
        img_dir = TMP_PATH if temp else IMG_PATH
        path = f"{img_dir}/" if is_abs else ""
        imgs = sorted(get_files_with_prefix(img_dir, prefix, path, only_one))
        if not temp:
            self.update_json(imgs)
        return imgs

    def update_imgs_json(self, imgs):
        """
        Add or update the properties related to images in the JSON representation of the digitization.
        :param imgs: list of image filenames (⚠ no absolute path!)
        """
        if type(imgs) is not list:
            imgs = get_files_with_prefix(IMG_PATH, f"{self.get_ref()}_", "")

        if not self.is_key_defined("imgs"):
            self.json["imgs"] = []

        # only unique filenames
        all_imgs = sorted(
            list(set([os.path.basename(img) for img in self.json["imgs"] + imgs]))
        )

        self.json["imgs"] = all_imgs
        self.json["img_nb"] = len(self.json["imgs"])
        self.json["zeros"] = self.img_zeros(self.json["imgs"][0])
        self.update(json=self.json)

    def update_json(self, imgs=Optional[List[str]]):
        if not imgs:
            imgs = sorted(get_files_with_prefix(IMG_PATH, f"{self.get_ref()}_", ""))

        json_data = {
            "id": self.id,
            "title": self.__str__(),
            "ref": self.get_ref(),
            "class": self.__class__.__name__,
            "type": get_name("Digitization"),
            "url": self.gen_manifest_url(),
            "imgs": imgs,
            "img_nb": len(imgs),
            "zeros": self.img_zeros(imgs[0] if imgs else 0),
        }
        type(self).objects.filter(pk=self.pk.__str__()).update(json=json_data)
        return self.json

    def to_json(self, reindex=True, no_img=False):
        djson = self.json or {}
        imgs = djson.get("imgs", [] if no_img else self.get_imgs(check_in_dir=True))
        return {
            "id": self.id,
            "title": self.__str__(),
            "ref": self.get_ref(),
            "class": self.__class__.__name__,
            "type": get_name("Digitization"),
            "url": self.gen_manifest_url(),
            "imgs": imgs,
            "img_nb": djson.get("img_nb", len(imgs)),
            "zeros": djson.get(
                "zeros", 0 if no_img else self.img_zeros(check_in_dir=reindex)
            ),
        }

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
                return (
                    manifest.toJSON(top=True)
                    if hasattr(manifest, "toJSON")
                    else manifest
                )
            except StructuralError as e:
                error["reason"] = f"{e}"
                return error
        return error

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

    def add_info(self, license_url):
        self.license = license_url
        if license_url != NO_LICENSE:
            self.is_open = True
        self.save(update_fields=["license", "source", "is_open"])


@receiver(post_save, sender=Digitization)
def digitization_post_save(sender, instance, created, **kwargs):
    if created:
        from app.webapp.tasks import convert_digitization

        transaction.on_commit(lambda: convert_digitization.delay(instance.id))


# Receive the pre_delete signal and delete the file associated with the model instance
@receiver(pre_delete, sender=Digitization)
def pre_delete_digit(sender, instance: Digitization, **kwargs):
    from app.webapp.tasks import delete_digitization

    other_media = instance.pdf.name if instance.digit_type == PDF_ABBR else None
    delete_digitization.delay(instance.get_ref(), other_media)

    # NOTE do not work because manifest_url uses the digitization id
    # from app.webapp.tasks import delete_regions
    # delete_regions.delay([r.id for r in instance.get_regions()])

    from app.webapp.utils.iiif.annotation import destroy_regions

    [destroy_regions(r) for r in instance.get_regions()]
