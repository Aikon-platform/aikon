from django.db import models

from app.webapp.models.edition import Edition

from app.webapp.models.utils.functions import get_fieldname


def get_name(fieldname, plural=False):
    return get_fieldname(fieldname, {}, plural)


class Volume(models.Model):
    class Meta:
        verbose_name = get_name("Volume")
        verbose_name_plural = get_name("Volume", True)
        app_label = "webapp"

    def __str__(self):
        return self.title

    title = models.CharField(
        verbose_name=get_name("title"), max_length=150, unique=True
    )
    edition = models.ForeignKey(
        Edition,
        verbose_name=get_name("Edition"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
