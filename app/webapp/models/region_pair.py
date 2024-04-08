from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.contrib.auth.models import User
from app.webapp.models.utils.functions import get_fieldname


def get_name(fieldname, plural=False):
    fields = {
        "RegionPair": {
            "en": "region pair",
            "fr": "paire de régions",
        },
    }
    return get_fieldname(fieldname, fields, plural)


class RegionPair(models.Model):
    class Meta:
        verbose_name = get_name("RegionPair")
        verbose_name_plural = get_name("RegionPair", True)
        app_label = "webapp"
        constraints = [
            models.UniqueConstraint(fields=["img_1", "img_2"], name="unique_img_pair")
        ]

    def __str__(self):
        return f"{self.img_1} | {self.img_2}"

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    # users = ArrayField(models.IntegerField(), blank=True, default=list)
    img_1 = models.CharField(max_length=150)
    img_2 = models.CharField(max_length=150)
    anno_ref_1 = models.CharField(max_length=150)  # Foreign key to Annotation ?
    anno_ref_2 = models.CharField(max_length=150)  # Foreign key to Annotation ?
    # category = models.IntegerField()
    categories = ArrayField(models.IntegerField(), blank=True, default=list)
    # user = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)
