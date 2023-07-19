from django.db import models

from app.webapp.models.digitization import Digitization
from app.webapp.models.utils.functions import get_fieldname


def get_name(fieldname, plural=False):
    return get_fieldname(fieldname, {}, plural)


class Annotation(models.Model):
    # TODO create annotation when the platform receives the response from the extractor API
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
    # NOTE model used to generate annotations
    model = models.CharField(max_length=150)

    def get_filename(self):
        return f"{self.digitization.get_filename()}_{self.id}"
