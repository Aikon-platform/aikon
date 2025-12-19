from __future__ import annotations  # for a reference to RegionPair from RegionPair

import re
from typing import List, NamedTuple

from django.core.exceptions import ValidationError
from django.contrib.postgres.fields import ArrayField
from django.db import models, connection
from django.db.models import Q, F

from app.webapp.utils.functions import cast, sort_key
from app.webapp.models.utils.functions import get_fieldname
from app.webapp.models.digitization import Digitization
from app.webapp.models.regions import Regions


class RegionPairTuple(NamedTuple):
    score: float
    q_img: str
    s_img: str
    q_regions: int
    s_regions: int
    category: int
    category_x: List[int]
    is_manual: bool
    similarity_type: int


def get_name(fieldname, plural=False):
    fields = {
        "RegionPair": {
            "en": "region pair",
            "fr": "paire de régions",
        },
    }
    return get_fieldname(fieldname, fields, plural)


class RegionPairManager(models.Manager):
    def bulk_update_or_create(self, objs, update_fields, match_field, update_field):
        if not objs:
            return

        model = self.model
        fields = [
            f
            for f in model._meta.fields
            if f.name in update_fields or f.name in match_field
        ]

        with connection.cursor() as cursor:
            table_name = model._meta.db_table
            columns = ", ".join(f.column for f in fields)
            placeholders = ", ".join("%s" for _ in fields)

            # conflict_update = ", ".join(
            #     f"{f.column} = EXCLUDED.{f.column}"
            #     for f in fields
            #     if f.name in update_fields and f.name != update_field
            # )
            #
            # if conflict_update:
            #     conflict_update += ", "
            # conflict_update += f"{update_field} = CASE WHEN EXCLUDED.{update_field} > {table_name}.{update_field} THEN EXCLUDED.{update_field} ELSE {table_name}.{update_field} END"
            #
            # sql = f"""
            #     INSERT INTO {table_name} ({columns})
            #     VALUES ({placeholders})
            #     ON CONFLICT ({', '.join(f.column for f in fields if f.name in match_field)})
            #     DO UPDATE SET {conflict_update}
            # """
            conflict_update = ", ".join(
                f"{f.column} = EXCLUDED.{f.column}"
                for f in fields
                if f.name in update_fields
            )

            # SQL query for bulk insert/update
            sql = f"""
                INSERT INTO {table_name} ({columns})
                VALUES ({placeholders})
                ON CONFLICT ({', '.join(f.column for f in fields if f.name in match_field)})
                DO UPDATE SET {conflict_update}
            """

            data = [[getattr(obj, f.name) for f in fields] for obj in objs]

            cursor.executemany(sql, data)


class RegionPair(models.Model):
    class Meta:
        verbose_name = get_name("RegionPair")
        verbose_name_plural = get_name("RegionPair", True)
        app_label = "webapp"
        constraints = [
            models.UniqueConstraint(fields=["img_1", "img_2"], name="unique_img_pair")
        ]
        # make database queries on those fields more efficient
        indexes = [
            models.Index(fields=["img_1"]),
            models.Index(fields=["img_2"]),
            models.Index(fields=["regions_id_1"]),
            models.Index(fields=["regions_id_2"]),
            models.Index(fields=["regions_id_1", "img_1"]),
            models.Index(fields=["regions_id_2", "img_2"]),
            models.Index(fields=["img_1", "regions_id_1", "regions_id_2"]),
            models.Index(fields=["img_2", "regions_id_1", "regions_id_2"]),
            models.Index(
                fields=["regions_id_1", "regions_id_2"],
                condition=Q(regions_id_1=F("regions_id_2")),
                name="idx_same_regions",
            ),
        ]

    def __str__(self):
        return (
            f"{self.img_1} (#{self.regions_id_1}) | {self.img_2} (#{self.regions_id_2})"
        )

    img_1 = models.CharField(max_length=150)  # ⚠️ must end with .jpg
    img_2 = models.CharField(max_length=150)  # ⚠️ must end with .jpg
    regions_id_1 = models.IntegerField()
    regions_id_2 = models.IntegerField()

    """
    Score of similarity between the two regions (only from automatic pairs)
    """
    score = models.FloatField(blank=True, null=True)
    """
    Category of the similarity
    1 = exact match
    2 = partial match
    3 = semantic match
    4 = no match
    """
    category = models.IntegerField(blank=True, null=True)
    """
    List of users Ids that have added this pair to their "user category" list
    """
    category_x = ArrayField(models.IntegerField(), null=True, default=list)
    """
    Is this pair manually added by a user or automatically generated (ie from a score file)
    """
    is_manual = models.BooleanField(max_length=150, null=True, default=False)
    """
    Type of similarity. This should replace `is_manual` in the long run
    1 = automatic / computed similarity
    2 = manual similarity
    3 = propagated similarity
    """
    similarity_type = models.IntegerField(blank=True, null=True, default=1)

    # TODO: consider removing the following fields to reduce overhead
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)

    objects = RegionPairManager()

    def get_info(self, q_img=None, as_json=False) -> RegionPairTuple | dict:
        if q_img is None:
            q_img = self.img_1
        s_img = self.img_2 if self.img_1 == q_img else self.img_1
        q_regions = self.regions_id_1 if self.img_1 == q_img else self.regions_id_2
        s_regions = self.regions_id_2 if self.img_1 == q_img else self.regions_id_1

        info = (
            self.score,
            q_img,
            s_img,
            q_regions,
            s_regions,
            self.category,
            self.category_x or [],
            self.is_manual,
            self.similarity_type,
        )
        if as_json:
            return {
                "score": info[0],
                "q_img": info[1],
                "s_img": info[2],
                "q_regions": info[3],
                "s_regions": info[4],
                "category": info[5],
                "category_x": info[6],
                "is_manual": info[7],
                "similarity_type": info[8],
            }
        return info

    def clean(self, regions_to_digit=None):
        """Validation supplémentaire avant save"""
        super().clean()

        # img1, img2 = self.img_1, self.img_2
        # rid1, rid2 = self.regions_id_1, self.regions_id_2
        #
        # def get_digit_id(img):
        #     return int(re.findall(r"\d+", img)[1])
        #
        # def get_digit_regions_id(digit_id):
        #     try:
        #         digit = Digitization.objects.get(id=digit_id)
        #     except Digitization.DoesNotExist:
        #         digit = None
        #     regions = list(digit.get_regions() if digit else [])
        #     if not regions:
        #         regions = Regions.objects.create(
        #             digitization=digit,
        #             model="manual",
        #         )
        #     else:
        #         regions = regions[0]
        #     return int(regions.id)
        #
        # if regions_to_digit is None:
        #     pass
        #
        #
        # # Vérifier que regions_id correspondent aux images
        # if self.regions_id_1 != regions_from_img(self.img_1):
        #     raise ValidationError(
        #         f"regions_id_1 ({self.regions_id_1}) doesn't match img_1 ({self.img_1})"
        #     )
        # if self.regions_id_2 != regions_from_img(self.img_2):
        #     raise ValidationError(
        #         f"regions_id_2 ({self.regions_id_2}) doesn't match img_2 ({self.img_2})"
        #     )

    def save(self, *args, **kwargs):
        """Auto-normalisation avant save"""
        self.full_clean()  # call clean() method
        super().save(*args, **kwargs)

    def to_dict(self) -> dict:
        return {
            "img_1": self.img_1,
            "img_2": self.img_2,
            "regions_id_1": self.regions_id_1,
            "regions_id_2": self.regions_id_2,
            "score": cast(self.score, float),
            "category": cast(self.category, int),
            "category_x": [cast(c, int) for c in self.category_x or []],
            "is_manual": self.is_manual,
            "similarity_type": cast(self.similarity_type, int),
        }

    def get_ref(self):
        return "-".join(sorted([self.img_1, self.img_2]))
