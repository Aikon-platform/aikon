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

    def get_absolute_edit_url(self):
        raise NotImplementedError("Subclasses must implement this method")

    def get_absolute_view_url(self):
        raise NotImplementedError("Subclasses must implement this method")

    def to_json(self, reindex=True, no_img=False):
        """
        reindex and no_img are used in subclasses to_json methods
        reindex: force recomputing all properties, even the one that require intensive computation
        no_img: if True, do not index image related property
        """
        try:
            return json_encode(
                {
                    "id": self.id.__str__(),
                    "class": self.__class__.__name__,
                    "type": get_fieldname(self.__class__.__name__),
                    "title": "",
                    "updated_at": None,
                    "edit_url": self.get_absolute_edit_url(),
                    "view_url": self.get_absolute_view_url(),
                    "user": "Unknown user",
                    "user_id": 0,
                }
            )
        except Exception as e:
            log(f"[to_json] Error", e)
            return None

    def update(self, **kwargs):
        type(self).objects.filter(pk=self.pk.__str__()).update(**kwargs)

    def get_json(self, reindex=False):
        """
        Get the JSON representation of the object.
        If reindex is True or json property hasn't been generated yet,
        generate the JSON and update the database.
        """
        if not self.json or reindex:
            json_data = self.to_json(reindex=True)
            type(self).objects.filter(pk=self.pk.__str__()).update(json=json_data)
            return json_data
        return self.json

    def is_key_defined(self, key):
        return not (not self.json or key not in self.json or not self.json[key])

    def get_key_value(self, key, default=None):
        if self.is_key_defined(key):
            return self.json[key]
        return default

    @classmethod
    def regenerate_all_json(cls):
        for obj in cls.objects.all():
            obj.get_json(reindex=True)


@receiver(post_save)
def generate_json(sender, instance, **kwargs):
    if isinstance(instance, AbstractSearchableModel):
        # from app.webapp.tasks import generate_record_json
        # generate_record_json.apply_async(
        #     args=[type(instance).__name__, instance.pk.__str__()],
        #     countdown=2  # 2-second delay to ensure record is saved in db
        # )
        try:
            json_data = instance.to_json(no_img=True)
            type(instance).objects.filter(pk=instance.pk.__str__()).update(
                json=json_data
            )
        except Exception as e:
            log(f"[generate_json] Error on json generation", e)
