import os
from glob import glob
from uuid import uuid4

from django.utils.safestring import mark_safe
from django.db import models
from iiif_prezi.factory import StructuralError
from app.config.settings import APP_URL, APP_NAME, APP_LANG, SAS_APP_URL
from app.similarity.const import SCORES_PATH
from app.webapp.models.digitization import Digitization
from app.webapp.models.searchable_models import AbstractSearchableModel
from app.webapp.models.utils.constants import WIT, REG
from app.webapp.models.utils.functions import get_fieldname
from app.webapp.utils.constants import MANIFEST_V2, MANIFEST_V1
from app.webapp.utils.paths import REGIONS_PATH


def get_name(fieldname, plural=False):
    return get_fieldname(fieldname, {}, plural)


def check_version(version):
    if version != MANIFEST_V1 and version != MANIFEST_V2:
        return MANIFEST_V1
    return version


class Regions(AbstractSearchableModel):
    class Meta:
        verbose_name = get_name("Regions")
        verbose_name_plural = get_name("Regions")
        app_label = "webapp"

    def __str__(self, light=False):
        if light:
            if self.json and "title" in self.json:
                return self.json["title"]
            return f'{get_name("Regions")} #{self.id}'

        witness = self.get_witness()
        if not witness:
            return f'{get_name("Regions")} #{self.id}'
        return f"{REG.capitalize()} #{self.id} | {witness.__str__()}"

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

    def img_nb(self):
        return self.get_digit().img_nb() or 0

    def img_zeros(self):
        return self.get_digit().img_zeros() or 0

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
                # return manifest.toJSON(top=True)
                return manifest
            except StructuralError as e:
                error["reason"] = f"{e}"
                return error
        return error

    def gen_mirador_url(self):
        return f"{SAS_APP_URL}/index.html?iiif-content={self.gen_manifest_url(version=MANIFEST_V2)}"

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

    def to_json(self, reindex=True):
        rjson = {} if reindex else self.json or {}
        digit = self.get_digit()

        return {
            "id": self.id,
            "title": self.__str__(),
            "ref": self.get_ref(),
            "class": self.__class__.__name__,
            "type": get_name("Regions"),
            "url": self.gen_mirador_url(),
            "img_nb": rjson.get("img_nb", digit.img_nb() if digit else 0),
            "zeros": rjson.get("zeros", digit.img_zeros() if digit else 0),
        }

    def get_annotations(self):
        from app.webapp.utils.iiif.annotation import get_regions_annotations

        return get_regions_annotations(self)

    def get_imgs(self, is_abs=False, only_one=False, check_in_dir=False):
        if digit := self.get_digit():
            return digit.get_imgs(
                is_abs=is_abs, only_one=only_one, check_in_dir=check_in_dir
            )
        return []

    def view_btn(self):
        from app.webapp.utils.iiif.gen_html import regions_btn

        action = "final" if self.is_validated else "edit"
        btn = regions_btn(self, action if self.has_regions() else "no_regions")

        if len(self.get_computed_pairs()) != 0:
            btn += regions_btn(self, "similarity")

        return mark_safe(btn)
