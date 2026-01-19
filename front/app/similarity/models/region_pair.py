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
from app.similarity.models.similarity_parameters import SimilarityParameters


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
    similarity_type: int
    similarity_hash: str


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
    def bulk_update_or_create(self, objs, update_fields, match_fields):
        if not objs:
            return

        model = self.model
        fields = [
            f
            for f in model._meta.fields
            if f.name in update_fields or f.name in match_fields
        ]

        with connection.cursor() as cursor:
            table_name = model._meta.db_table
            columns = ", ".join(f.column for f in fields)
            placeholders = ", ".join("%s" for _ in fields)
            conflict_update = ", ".join(
                f"{f.column} = EXCLUDED.{f.column}"
                for f in fields
                if f.name in update_fields
            )

            sql = f"""
                INSERT INTO {table_name} ({columns})
                VALUES ({placeholders})
                ON CONFLICT ({', '.join(f.column for f in fields if f.name in match_fields)})
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
            models.UniqueConstraint(
                fields=["img_1", "img_2", "similarity_hash"], name="unique_img_pair"
            )
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
    Type of similarity.
    1 =_pair  automatic / computed similarity
    2 = manual similarity
    3 = propagated similarity
    """
    similarity_type = models.IntegerField(blank=True, null=True, default=1)
    """
    Hash of the parameters used to compute the similarity (for automatic similarities)
    """
    similarity_hash = models.CharField(
        max_length=8, blank=True, null=True, default=None
    )

    objects = RegionPairManager()

    @classmethod
    def order_pair(
        cls, pair: tuple | str, as_string: bool = False
    ) -> tuple[str, str] | str:
        """Return image names ordered consistently"""
        ref1, ref2 = pair.split("-") if isinstance(pair, str) else pair
        if sort_key(ref2) < sort_key(ref1):
            ref1, ref2 = ref2, ref1
        return f"{ref1}-{ref2}" if as_string else (ref1, ref2)

    @classmethod
    def rid_from_pair_containing_img(
        cls, img: str, similarity_hash: str = None, create_if_missing: bool = True
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

        # Try to find in existing pairs (priority to specific hash if provided)
        filter_kwargs = {"img_1": img}
        if similarity_hash:
            filter_kwargs["similarity_hash"] = similarity_hash

        q1 = (
            cls.objects.filter(**filter_kwargs)
            .values_list("regions_id_1", flat=True)
            .first()
        )
        if q1:
            return q1

        filter_kwargs = {"img_2": img}
        if similarity_hash:
            filter_kwargs["similarity_hash"] = similarity_hash

        q2 = (
            cls.objects.filter(**filter_kwargs)
            .values_list("regions_id_2", flat=True)
            .first()
        )
        if q2:
            return q2

        digit_id = extract_digit_id(img)
        if digit_id is None:
            raise ValidationError(f"Cannot extract digitization ID from {img}")

        return get_digit_regions_id(digit_id, create_if_missing)

    @classmethod
    def rid_from_img(
        cls,
        img: str,
        candidate_rids: list[int] = None,
        similarity_hash: str = None,
        create_if_missing=True,
    ) -> int:
        """
        Get regions_id for an image.
        Priority:
        1. candidate_rid matching image's digitization (order of candidate_rids matters)
        2. Any valid candidate_rid (if digit validation fails)
        3. Existing pair containing the image
        4. Create new regions (if create_if_missing=True)
        """
        img = add_jpg(img)
        img_digit_id = extract_digit_id(img)

        valid_candidates = [rid for rid in (candidate_rids or []) if rid is not None]
        if valid_candidates:
            if img_digit_id is not None:
                for rid in valid_candidates:
                    try:
                        if get_region_digit_id(rid) == img_digit_id:
                            return rid
                    except Exception:
                        continue

            # No match found: return first existing candidate (skip DB validation if Digitization missing)
            return valid_candidates[0]

        return cls.rid_from_pair_containing_img(img, similarity_hash, create_if_missing)

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

    def get_parameters(self) -> dict | None:
        """Get similarity parameters from hash"""
        if not self.similarity_hash:
            return None
        return SimilarityParameters.get_params(self.similarity_hash)

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
            self.similarity_type,
            self.similarity_hash,
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
                "similarity_type": info[7],
                "similarity_hash": info[8],
            }
        return info

    def to_dict(self) -> dict:
        return {
            "img_1": self.img_1,
            "img_2": self.img_2,
            "regions_id_1": self.regions_id_1,
            "regions_id_2": self.regions_id_2,
            "score": cast(self.score, float),
            "category": cast(self.category, int),
            "category_x": [cast(c, int) for c in self.category_x or []],
            "similarity_type": cast(self.similarity_type, int),
            # "similarity_params": self.get_parameters()
        }

    def get_ref(self):
        return "-".join(sorted([self.img_1, self.img_2]))
