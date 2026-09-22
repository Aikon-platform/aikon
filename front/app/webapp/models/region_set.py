from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Q

from app.webapp.models.searchable_models import AbstractSearchableModel, json_encode
from app.webapp.models.utils.functions import get_fieldname
from app.webapp.models.utils.constants import NO_USER

from django.urls import reverse

from app.webapp.utils.logger import log


def get_name(fieldname, plural=False):
    fields = {
        "RegionSet": {
            "en": "region set",
            "fr": "set de regions",
        },
    }
    return get_fieldname(fieldname, fields, plural)


class RegionSet(AbstractSearchableModel):
    class Meta:
        verbose_name = get_name("RegionSet")
        verbose_name_plural = get_name("RegionSet", plural=True)
        app_label = "webapp"

    def __str__(self, light=False):
        if light and self.json and "title" in self.json:
            return self.json["title"]

        if self.length() != 1:
            return f"{self.title} ({self.length()} regions)"
        return self.title

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    title = models.CharField(max_length=50)
    is_public = models.BooleanField(default=False)

    region_ids = ArrayField(models.CharField(max_length=50), default=list, blank=True, null=True)

    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)

    # todo change for ManyToManyField
    shared_with = ArrayField(models.IntegerField(), default=list, blank=True, null=True)

    selection = models.JSONField(
        verbose_name="JSON selection",
        blank=True,
        null=True,
    )

    def length(self):
        return sum(
            len(field or [])
            for field in self.region_ids
        )

    def get_treatments(self):
        return self.treatments.all()

    @property
    def regions(self):
        if not self.region_ids:
            return []
        # TODO RegionSet voir quoi retourner
        return list()

    @property
    def region_names(self):
        # TODO RegionSet voir quoi retourner
        return [self.regions]

    def get_region_metadata(self):
        # TODO RegionSet voir quoi retourner
        def obj_meta(obj):
            return {
                "id": obj.id,
                "title": obj.__str__(),
                "url": obj.get_absolute_view_url(),
            }

        selection = {
            "Regions": {},
        }
        return selection

    def get_treatment_metadata(self):
        def meta(treatment):
            return {
                "id": treatment.id.__str__(),
                "status": treatment.status,
                "task_type": treatment.task_type,
                "url": treatment.get_absolute_view_url(),
            }

        return {
            treatment.id.__str__(): meta(treatment)
            for treatment in self.get_treatments()
        }

    def get_absolute_edit_url(self):
        # TODO create view to edit region set without loading it
        # return reverse("region_set", args=[self.id])
        return ""

    def get_absolute_view_url(self):
        # TODO create view to view regions from region set?
        return reverse("webapp:region_set_view", args=[self.id])

    def get_selection(self, reindex=False):
        if not self.selection or reindex:
            json_data = {
                "id": self.id,
                "type": "regionSet",
                "title": self.title,
                "owner_id": self.user.id,
                "is_public": self.is_public,
                "selected": self.get_region_metadata(),
            }
            type(self).objects.filter(pk=self.pk).update(selection=json_data)
        return self.selection

    def to_json(self, reindex=True, no_img=False):
        user = self.user
        try:
            return json_encode(
                {
                    "id": self.id,
                    "class": self.__class__.__name__,
                    "type": get_name("RegionSet"),
                    "title": self.__str__(),
                    "user_id": user.id if user else 0,
                    "user": user.__str__() if user else NO_USER,
                    "edit_url": self.get_absolute_edit_url(),
                    "view_url": self.get_absolute_view_url(),
                    "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M")
                    if self.updated_at
                    else "-",
                    "is_public": self.is_public,
                    "selection": self.get_selection(reindex),
                    "treatments": self.get_treatment_metadata(),
                }
            )
        except Exception as e:
            log(f"[to_json] Error", e)
            return None