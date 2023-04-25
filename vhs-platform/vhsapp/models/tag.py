from django.db import models

from vhsapp.models.utils.functions import get_fieldname


def get_name(fieldname, plural=False):
    return get_fieldname(fieldname, {}, plural)


class Tag(models.Model):
    class Meta:
        verbose_name = get_name("Tag")
        verbose_name_plural = get_name("Tag", True)

    def __str__(self):
        return self.label

    label = models.CharField(max_length=50)


"""
tag = Tag.objects.get(label='Astronomy')
witnesses = tag.witness_set.all()
"""
