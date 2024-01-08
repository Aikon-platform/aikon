from glob import glob
from uuid import uuid4

from django.contrib.postgres.fields import ArrayField
from django.utils.safestring import mark_safe
from django.db import models
from iiif_prezi.factory import StructuralError

from app.config.settings import APP_URL, APP_NAME
from app.webapp.models.digitization import Digitization
from app.webapp.models.utils.functions import get_fieldname
from app.webapp.models.witness import Witness
from app.webapp.utils.constants import MANIFEST_V2, MANIFEST_V1
from app.webapp.utils.paths import BASE_DIR, ANNO_PATH


def get_name(fieldname, plural=False):
    return get_fieldname(fieldname, {}, plural)


def check_version(version):
    if version != MANIFEST_V1 and version != MANIFEST_V2:
        return MANIFEST_V1
    return version


class Annotation(models.Model):
    class Meta:
        verbose_name = get_name("Annotation")
        verbose_name_plural = get_name("Annotation", True)
        app_label = "webapp"

    def __str__(self):
        witness = self.get_witness()
        return f"Witness #{witness.id}: {witness}"

    digitization = models.ForeignKey(
        Digitization,
        related_name="annotations",  # to access the all annotations from Digitization
        verbose_name=get_name("Digitization"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    # NOTE machine learning model used to generate annotations
    model = models.CharField(max_length=150)
    # # TODO check if useful
    # anno_ids = ArrayField(models.CharField(max_length=150), blank=True, null=True)
    is_validated = models.BooleanField(default=False)

    def get_digit(self):
        try:
            return self.digitization
        except AttributeError:
            return None

    def get_witness(self):
        if digit := self.digitization:
            return digit.get_witness()
        return None

    def gen_manifest_url(self, only_base=False, version=MANIFEST_V1):
        witness = self.get_witness()
        digit = self.get_digit()
        if not witness or not digit:
            return None

        base_url = (
            f"{APP_URL}/{APP_NAME}/iiif/{check_version(version)}/{self.get_ref()}"
        )
        return f"{base_url}{'' if only_base else '/manifest.json'}"

    def gen_manifest_json(self, version=MANIFEST_V1):
        from app.webapp.utils.iiif.manifest import gen_manifest_json

        error = {"error": "Unable to create a valid manifest"}
        if manifest := gen_manifest_json(self, check_version(version)):
            try:
                return manifest.toJSON(top=True)
            except StructuralError as e:
                error["reason"] = f"{e}"
                return error
        return error

    def get_ref(self):
        if digit := self.get_digit():
            # anno_prefix = f"{wit_abbr}{wit_id}_{digit_abbr}{digit_id}_anno{anno_id}"
            return f"{digit.get_ref()}_anno{self.id}"
        return None

    def get_filename(self):
        return f"{self.get_ref()}.txt"

    def gen_anno_id(self, canvas_nb, save_id=False):
        # anno_id = f"{wit_abbr}{wit_id}_{digit_abbr}{digit_id}_anno{anno_id}_c{canvas_nb}_{uuid4().hex[:8]}"
        anno_id = f"{self.get_ref()}_c{canvas_nb}_{uuid4().hex}"

        # # TODO check if it is necessary
        # if save_id:
        #     self.anno_ids.append(anno_id)
        #     self.save()
        return anno_id

    def has_annotations(self):
        # if there is an annotation file named after the current Annotation
        if len(glob(f"{ANNO_PATH}/{self.get_ref()}.txt")):
            return True
        return False

    def get_metadata(self):
        if digit := self.get_digit():
            metadata = digit.get_metadata()
            # {wit_abbr}{wit_id}_{digit_abbr}{digit_id}_anno{anno_id}
            metadata["@id"] = self.get_ref()

            return metadata
        return {}

    def get_imgs(self):
        if digit := self.get_digit():
            return digit.get_imgs()
        return []

    def view_btn(self):
        from app.webapp.utils.iiif.gen_html import anno_btn

        action = "final" if self.is_validated else "edit"
        return mark_safe(
            anno_btn(
                self,
                action if self.has_annotations() else "no_anno",
            )
        )

    # def view_anno(self, obj: Digitization):
    #     # TODO here multiple button for multiple annotation
    #     if obj.id and obj.has_images():
    #         action = "final" if obj.is_validated else "edit"
    #         if not obj.has_annotations():
    #             action = "no_anno"
    #         # todo loop on linked annotations.
    #         # return gen_btn(obj.id, action, MANIFEST_V2, obj.get_wit_type())
    #     return "-"
