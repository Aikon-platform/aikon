from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver

from app.webapp.models.content import Content
from app.webapp.models.series import Series
from app.webapp.models.person import Person
from app.webapp.models.utils.constants import ROLES

from app.webapp.models.utils.functions import get_fieldname


def get_name(fieldname, plural=False):
    fields = {
        "source": {"en": "digitization source", "fr": "source de la numérisation"},
    }
    return get_fieldname(fieldname, fields, plural)


class Role(models.Model):
    class Meta:
        verbose_name = get_name("Role")
        verbose_name_plural = get_name("Role", True)
        app_label = "webapp"

    def __str__(self):
        name = self.person.name if self.person else get_name("unknown")
        role = dict(ROLES).get(self.role) if self.role else get_name("no_role")
        return f"{name} ({role})"

    content = models.ForeignKey(
        Content,
        verbose_name=get_name("Content"),
        related_name="roles",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    series = models.ForeignKey(
        Series,
        related_name="roles",
        verbose_name=get_name("Series"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    person = models.ForeignKey(
        Person,
        verbose_name=get_name("Person"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    role = models.CharField(
        verbose_name=get_name("Role"),
        choices=ROLES,
        max_length=150,
        blank=True,
    )

    def get_role(self):
        return dict(ROLES).get(self.role) if self.role else get_name("no_role")

    def get_role_abbr(self):
        return self.role

    def save(self, *args, **kwargs):
        if self.role == "" and self.person is None:
            # delete role record if person and role are set to null
            self.delete()
        else:
            super().save(*args, **kwargs)
