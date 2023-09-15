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
    # NOTE machine learning model used to generate annotations
    model = models.CharField(max_length=150)
    # NOTE canvas nb on which the annotation can be found
    canvas = models.IntegerField(
        null=True,
        blank=True,
    )

    def get_filename(self):
        # TODO here indicate canvas nb
        # TODO store id for SAS that use a random string of char
        return f"{self.digitization.get_filename()}_{self.id}"
