from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.db import models
from app.webapp.models.utils.functions import get_fieldname


def get_name(fieldname, plural=False):
    fields = {
        "DocumentSet": {
            "en": "document set",
            "fr": "panier de documents",
        },
    }
    return get_fieldname(fieldname, fields, plural)


class DocumentSet(models.Model):
    class Meta:
        verbose_name = get_name("DocumentSet")
        verbose_name_plural = get_name("DocumentSet", True)
        app_label = "webapp"

    def __str__(self):
        return self.name

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=150)
    wit_ids = ArrayField(models.IntegerField(), default=list)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)
