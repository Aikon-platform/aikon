import json
from uuid import UUID

from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save

from app.webapp.models.utils.functions import get_fieldname
from app.webapp.utils.logger import log


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


def json_encode(data):
    return json.loads(json.dumps(data, cls=UUIDEncoder))


class AbstractSearchableModel(models.Model):
    class Meta:
        abstract = True
        app_label = "webapp"

    json = models.JSONField(
        verbose_name="JSON representation",
        blank=True,
        null=True,
    )

    def get_absolute_url(self):
        raise NotImplementedError("Subclasses must implement this method")

    def to_json(self, reindex=True):
        try:
            return json_encode(
                {
                    "id": self.id.__str__(),
                    "class": self.__class__.__name__,
                    "type": get_fieldname(self.__class__.__name__),
                    "title": "",
                    "updated_at": None,
                    "url": self.get_absolute_url(),
                    "user": "Unknown user",
                    "user_id": 0,
                }
            )
        except Exception as e:
            log(f"[to_json] Error", e)
            return None

    def get_json(self, reindex=False):
        if not self.json or reindex:
            json_data = self.to_json(reindex=True)
            type(self).objects.filter(pk=self.pk.__str__()).update(json=json_data)
            return json_data
        return self.json

    @classmethod
    def regenerate_all_json(cls):
        for obj in cls.objects.all():
            obj.get_json(reindex=True)


@receiver(post_save)
def generate_json(sender, instance, **kwargs):
    if isinstance(instance, AbstractSearchableModel):
        try:
            json_data = instance.to_json()
            type(instance).objects.filter(pk=instance.pk.__str__()).update(
                json=json_data
            )
        except Exception as e:
            log(f"[generate_json] Error on json generation", e)
