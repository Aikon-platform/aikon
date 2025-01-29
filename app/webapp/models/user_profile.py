from django.db import models
from django.contrib.auth.models import User

from app.webapp.models.utils.functions import get_fieldname


def get_name(fieldname, plural=False):
    fields = {
        "picture": {"en": "picture", "fr": "image"},
        "role": {"en": "role", "fr": "rôle"},
        "affiliation": {"en": "affiliation", "fr": "affiliation"},
        "presentation": {"en": "presentation", "fr": "présentation"},
    }
    return get_fieldname(fieldname, fields, plural)


class UserProfile(models.Model):
    class Meta:
        verbose_name = get_name("UserProfile")
        verbose_name_plural = get_name("UserProfile", True)
        app_label = "webapp"

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    picture = models.ImageField(
        verbose_name=get_name("picture"),
        upload_to="picture/",
        blank=True,
    )
    role = models.CharField(verbose_name=get_name("role"), max_length=200, blank=True)
    affiliation = models.CharField(
        verbose_name=get_name("affiliation"), max_length=200, blank=True
    )
    presentation = models.TextField(
        verbose_name=get_name("presentation"), max_length=3000, blank=True
    )
