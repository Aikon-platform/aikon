import os
from glob import glob
from uuid import uuid4

from django.utils.safestring import mark_safe
from django.db import models
from iiif_prezi.factory import StructuralError

from app.config.settings import APP_URL, APP_NAME, APP_LANG
from app.similarity.const import SCORES_PATH
from app.webapp.models.digitization import Digitization
from app.webapp.models.utils.constants import WIT
from app.webapp.models.utils.functions import get_fieldname
from app.webapp.utils.constants import MANIFEST_V2, MANIFEST_V1
from app.webapp.utils.paths import REGIONS_PATH


def get_name(fieldname, plural=False):
    return get_fieldname(fieldname, {}, plural)


def check_version(version):
    if version != MANIFEST_V1 and version != MANIFEST_V2:
        return MANIFEST_V1
    return version


class Regions(models.Model):
    class Meta:
        verbose_name = get_name("Regions")
        verbose_name_plural = get_name("Regions")
        app_label = "webapp"

    def __str__(self):
        witness = self.get_witness()
        space = "" if APP_LANG == "en" else " "
        return f"{WIT.capitalize()} #{witness.id}{space}: {witness}"

    digitization = models.ForeignKey(
        Digitization,
        related_name="regions",  # to access the all regions from Digitization
        verbose_name=get_name("Digitization"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    # NOTE machine learning model used to generate annotations
    model = models.CharField(max_length=150)
    # # TODO check if useful
    # region_ids = ArrayField(models.CharField(max_length=150), blank=True, null=True)
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
            # regions_prefix = f"{wit_abbr}{wit_id}_{digit_abbr}{digit_id}_anno{regions_id}"
            return f"{digit.get_ref()}_anno{self.id}"
        return None

    def get_filename(self):
        return f"{self.get_ref()}.txt"

    def gen_annotation_id(self, canvas_nb, save_id=False):
        # annotation_id = f"{wit_abbr}{wit_id}_{digit_abbr}{digit_id}_anno{regions_id}_c{canvas_nb}_{uuid4().hex[:8]}"
        annotation_id = f"{self.get_ref()}_c{canvas_nb}_{uuid4().hex}"

        # # TODO check if it is necessary
        # if save_id:
        #     self.annotation_ids.append(annotation_id)
        #     self.save()
        return annotation_id

    def has_regions(self):
        # if there is a regions file named after the current Regions
        if len(glob(f"{REGIONS_PATH}/{self.get_ref()}.txt")):
            return True
        return False

    def get_computed_pairs(self):
        sim_files = [
            npy_file
            for npy_file in os.listdir(SCORES_PATH)
            if self.get_ref() in npy_file
        ]
        return sim_files

    def get_metadata(self):
        if digit := self.get_digit():
            metadata = digit.get_metadata()
            # {wit_abbr}{wit_id}_{digit_abbr}{digit_id}_anno{regions_id}
            metadata["@id"] = self.get_ref()

            return metadata
        return {}

    def get_annotations(self):
        from app.webapp.utils.iiif.annotation import get_regions_annotations

        return get_regions_annotations(self)

    def get_imgs(self):
        if digit := self.get_digit():
            return digit.get_imgs()
        return []

    def view_btn(self):
        from app.webapp.utils.iiif.gen_html import regions_btn

        action = "final" if self.is_validated else "edit"
        btn = regions_btn(self, action if self.has_regions() else "no_regions")

        if len(self.get_computed_pairs()) != 0:
            btn += regions_btn(self, "similarity")

        return mark_safe(btn)
