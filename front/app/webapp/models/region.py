from django.db import models
from webapp.models.searchable_models import AbstractSearchableModel
from app.webapp.models.region_extraction import RegionExtraction
from app.webapp.models.tag import Tag
from app.webapp.models.utils.functions import get_fieldname


def get_name(fieldname, plural=False):
    fields = {
        "Region": {
            "en": "region",
            "fr": "région",
        },
    }
    return get_fieldname(fieldname, fields, plural)


class Region(AbstractSearchableModel):
    class Meta:
        verbose_name = get_name("Region")
        verbose_name_plural = get_name("Region", plural=True)
        app_label = "webapp"

    def __str__(self, light=False):
        return

    region_extraction = models.ForeignKey(
        RegionExtraction,
        related_name="regions",  # to access the regions from RegionExtraction
        verbose_name=get_name("RegionExtraction"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    notes = models.TextField(
        verbose_name=get_name("notes"), max_length=3000, blank=True
    )

    tags = models.ManyToManyField(
        Tag,
        verbose_name=get_name("Tag"),
        blank=True,
    )

    def get_region_extraction(self):
        if region_extraction := self.region_extraction:
            return region_extraction
        return None
