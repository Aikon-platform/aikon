from glob import glob
from uuid import uuid4

from django.contrib.postgres.fields import ArrayField
from django.db import models
from iiif_prezi.factory import StructuralError

from app.webapp.models.digitization import Digitization
from app.webapp.models.utils.functions import get_fieldname
from app.webapp.models.witness import Witness
from app.webapp.utils.constants import MANIFEST_V2
from app.webapp.utils.iiif import get_manifest_url_base
from app.webapp.utils.iiif.manifest import gen_manifest_json
from app.webapp.utils.paths import BASE_DIR, ANNO_PATH


def get_name(fieldname, plural=False):
    return get_fieldname(fieldname, {}, plural)


class Annotation(models.Model):
    class Meta:
        verbose_name = get_name("Annotation")
        verbose_name_plural = get_name("Annotation", True)
        app_label = "webapp"

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
    anno_ids = ArrayField(models.CharField(max_length=150), blank=True, null=True)
    is_validated = models.BooleanField(default=False)

    def get_digit(self) -> Digitization | None:
        try:
            return self.digitization
        except AttributeError:
            return None

    def get_witness(self) -> Witness | None:
        if digit := self.digitization:
            return digit.get_witness()
        return None

    def gen_manifest_url(self, only_base=False):
        witness = self.get_witness()
        digit = self.get_digit()
        if not witness or not digit:
            return None

        base_url = (
            f"{get_manifest_url_base()}/{MANIFEST_V2}/{witness.id}/{digit.id}/{self.id}"
        )
        return f"{base_url}{'' if only_base else '/manifest.json'}"

    def gen_manifest_json(self):
        error = {"error": "Unable to create a valid manifest"}
        if manifest := gen_manifest_json(self):
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
        anno_id = f"{self.get_ref()}_c{canvas_nb}_{uuid4().hex[:8]}"

        # TODO check if it is necessary
        if save_id:
            self.anno_ids.append(anno_id)
            self.save()
        return anno_id

    def has_annotations(self):
        # if there is an annotation file named after the current Annotation
        if len(glob(f"{BASE_DIR}/{ANNO_PATH}/{self.get_ref()}.txt")):
            return True
        return False

    def get_metadate(self):
        if digit := self.get_digit():
            metadata = digit.get_metadata()
            # TODO check if other metadata are needed
            return metadata
        return {}

    def get_imgs(self):
        if digit := self.get_digit():
            return digit.get_imgs()
        return []
