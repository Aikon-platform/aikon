from uuid import uuid4

from django.db import models

from app.webapp.models.digitization import Digitization
from app.webapp.models.utils.functions import get_fieldname


def get_name(fieldname, plural=False):
    return get_fieldname(fieldname, {}, plural)


class Annotation(models.Model):
    # TODO create annotation when the platform receives the response from the extractor API
    # NOTE one Annotation obj is linked to an annotation file => one Digit can have multiple Annotations
    # One Annotation is linked to
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

    def get_anno_prefix(self):
        # filename = f"{wit_abbr}{wit_id}_{digit_abbr}{digit_id}_anno{anno_id}"
        return f"{self.digitization.get_filename()}_anno{self.id}"

    def get_filename(self):
        return f"{self.get_anno_prefix()}.txt"

    def gen_anno_id(self, canvas_nb):
        # OLD anno_id = f"{wit_abbr}-{wit_id}-{canvas_nb}-{anno_nb}"
        # TODO : find how to store generated anno_ids + to delete anno_ids that were deleted
        return f"{self.get_anno_prefix()}_c{canvas_nb}_{uuid4().hex[:8]}"
