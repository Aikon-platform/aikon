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


def extract_digit_id(img: str) -> int | None:
    """Extract digitization ID from image name (e.g., 'wit7_man9_0023_...' → 9)"""
    matches = re.findall(r"\d+", img)
    return int(matches[1]) if len(matches) > 1 else None


def get_region_digit_id(regions_id: int) -> int | None:
    """Get digitization ID associated with a regions_id"""
    try:
        region = Regions.objects.select_related("digitization").get(id=regions_id)
        return region.digitization.id if region.digitization else None
    except Regions.DoesNotExist:
        return None


def get_digit_regions_id(digit_id: int, create_if_missing: bool = False) -> int:
    """Get or create regions_id for a digitization ID"""
    regions = Regions.objects.filter(digitization_id=digit_id).first()

    if not regions:
        if create_if_missing:
            try:
                digit = Digitization.objects.get(id=digit_id)
            except Digitization.DoesNotExist:
                raise ValidationError(f"Digitization {digit_id} does not exist")

            regions = Regions.objects.create(digitization=digit, model="manual")
        else:
            raise ValidationError(f"No regions found for digitization {digit_id}")

    return regions.id


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


def add_jpg(img: str) -> str:
    return img if img.endswith(".jpg") else f"{img}.jpg"


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
    category_x = ArrayField(models.IntegerField(), null=True, blank=True, default=list)
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

    @classmethod
    def rid_from_pair_containing_img(
        cls, img: str, create_if_missing: bool = True
    ) -> int:
        """
        Retrieve regions_id for an image, with fallback to extraction from image name.
        Priority:
        1. Existing pair with img_1
        2. Existing pair with img_2
        3. Extract from image name and lookup/create regions
        """
        if not img.endswith(".jpg"):
            img = f"{img}.jpg"

        # Try to find in existing pairs
        q1 = cls.objects.values_list("regions_id_1").filter(img_1=img).first()
        if q1:
            return q1[0]

        q2 = cls.objects.values_list("regions_id_2").filter(img_2=img).first()
        if q2:
            return q2[0]

        # Extract from image name
        digit_id = extract_digit_id(img)
        if digit_id is None:
            raise ValidationError(f"Cannot extract digitization ID from {img}")

        return get_digit_regions_id(digit_id, create_if_missing)

    @classmethod
    def rid_from_img(
        cls, img: str, candidate_rids: list[int] = None, create_if_missing=True
    ) -> int:
        """
        Get regions_id for an image.
        Checks candidate_rids first (in order), then falls back to existing pairs or creation.
        """
        img = add_jpg(img)
        img_digit_id = extract_digit_id(img)

        if img_digit_id is None:
            raise ValidationError(f"Cannot extract digitization ID from {img}")

        if candidate_rids:
            for rid in candidate_rids:
                if get_region_digit_id(rid) == img_digit_id:
                    return rid

        return cls.rid_from_pair_containing_img(img, create_if_missing)

    @classmethod
    def check_order(
        cls, img1, img2, rid1, rid2, regions_to_digit=None, create_missing_regions=False
    ):
        """Return regions IDs ordered according to image names"""
        if sort_key(img2) < sort_key(img1):
            img1, img2 = img2, img1
            rid1, rid2 = rid2, rid1
        else:
            img1, img2 = img1, img2

        # Extract digitization IDs from images
        img_digit_id_1 = extract_digit_id(img1)
        img_digit_id_2 = extract_digit_id(img2)

        if img_digit_id_1 is None or img_digit_id_2 is None:
            raise ValidationError(
                f"Cannot extract digitization ID from image names " f"({img1}, {img2})"
            )

        # Get digitization IDs from regions (with optional cache)
        if regions_to_digit:
            reg_digit_id_1 = regions_to_digit.get(rid1) or None
            reg_digit_id_2 = regions_to_digit.get(rid2) or None
        else:
            reg_digit_id_1 = get_region_digit_id(rid1)
            reg_digit_id_2 = get_region_digit_id(rid2)

        # Fix mismatches
        if img_digit_id_1 != reg_digit_id_1:
            if img_digit_id_2 == reg_digit_id_1 and img_digit_id_1 == reg_digit_id_2:
                rid1, rid2 = rid2, rid1
                reg_digit_id_1, reg_digit_id_2 = reg_digit_id_2, reg_digit_id_1
            else:
                rid1 = get_digit_regions_id(img_digit_id_1, create_missing_regions)

        if img_digit_id_2 != reg_digit_id_2:
            rid2 = get_digit_regions_id(img_digit_id_2, create_missing_regions)

        return img1, img2, rid1, rid2

    def clean(self, regions_to_digit=None, create_missing_regions=False):
        super().clean()

        self.img_1, self.img_2, self.regions_id_1, self.regions_id_2 = self.check_order(
            add_jpg(self.img_1),
            add_jpg(self.img_2),
            self.regions_id_1,
            self.regions_id_2,
            regions_to_digit,
            create_missing_regions,
        )

    def save(self, validate=False, *args, **kwargs):
        if validate:
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
