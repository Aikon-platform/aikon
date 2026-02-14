from __future__ import annotations  # for a reference to RegionPair from RegionPair

import re
from typing import List, NamedTuple

from django.contrib.postgres.fields import ArrayField
from django.db import models, connection

from app.webapp.utils.functions import cast
from app.webapp.models.utils.functions import get_fieldname
from app.similarity.models.similarity_parameters import SimilarityParameters

IMG_RE = re.compile(r"^wit(\d+)_(\w{3})(\d+)_(\d+)(?:_([\d,]+))?\.jpg$")


class ImgRef(NamedTuple):
    wit: int
    digit_type: str
    digit: int
    page: int
    bbox: str | None  # None = page-level


def parse_img(img: str) -> ImgRef:
    m = IMG_RE.match(img)
    if not m:
        raise ValueError(f"Invalid image name: {img}")
    return ImgRef(
        wit=int(m.group(1)),
        digit_type=m.group(2),
        digit=int(m.group(3)),
        page=int(m.group(4)),
        bbox=m.group(5),
    )


class RegionPairTuple(NamedTuple):
    score: float
    q_img: str
    s_img: str
    q_digit: int
    s_digit: int
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
                fields=["img_1", "img_2", "similarity_hash"],
                name="unique_img_pair",
            ),
            models.CheckConstraint(
                check=models.Q(img_1__lte=models.F("img_2")),
                name="pair_ordering",
            ),
        ]

        indexes = [
            models.Index(fields=["digit_1", "digit_2"]),
            models.Index(fields=["digit_1", "digit_2", "score"]),
            models.Index(fields=["img_1", "img_2"]),
            models.Index(fields=["img_1"]),
            models.Index(fields=["img_2"]),
            models.Index(fields=["category"]),
            models.Index(
                fields=["digit_1", "digit_2"],
                condition=models.Q(digit_1=models.F("digit_2")),
                name="idx_same_digit",
            ),
        ]

    def __str__(self):
        return f"{self.img_1} (d#{self.digit_1}) | {self.img_2} (d#{self.digit_2})"

    img_1 = models.CharField(max_length=150)  # ⚠️ must end with .jpg
    img_2 = models.CharField(max_length=150)  # ⚠️ must end with .jpg

    # TO BE DELETED
    regions_id_1 = models.IntegerField(null=True, blank=True)
    regions_id_2 = models.IntegerField(null=True, blank=True)

    digit_1 = models.IntegerField(null=True)  # nullable for backfill
    digit_2 = models.IntegerField(null=True)  # nullable for backfill

    anno_1 = models.CharField(max_length=64, null=True, blank=True)
    anno_2 = models.CharField(max_length=64, null=True, blank=True)

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
        if str(ref2) < str(ref1):
            ref1, ref2 = ref2, ref1
        return f"{ref1}-{ref2}" if as_string else (ref1, ref2)

    def clean(self):
        super().clean()
        self.img_1 = add_jpg(self.img_1)
        self.img_2 = add_jpg(self.img_2)

        if self.img_2 < self.img_1:
            self.img_1, self.img_2 = self.img_2, self.img_1
            self.regions_id_1, self.regions_id_2 = self.regions_id_2, self.regions_id_1
            self.anno_1, self.anno_2 = self.anno_2, self.anno_1

        for side in ("1", "2"):
            ref = parse_img(getattr(self, f"img_{side}"))
            setattr(self, f"digit_{side}", ref.digit)

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
        is_q1 = self.img_1 == q_img
        s_img = self.img_2 if is_q1 else self.img_1
        q_digit = self.digit_1 if is_q1 else self.digit_2
        s_digit = self.digit_2 if is_q1 else self.digit_1

        info = (
            self.score,
            q_img,
            s_img,
            q_digit,
            s_digit,
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
                "q_digit": info[3],
                "s_digit": info[4],
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
            "digit_1": self.digit_1,
            "digit_2": self.digit_2,
            "anno_1": self.anno_1,
            "anno_2": self.anno_2,
            "score": cast(self.score, float),
            "category": cast(self.category, int),
            "category_x": [cast(c, int) for c in self.category_x or []],
            "similarity_type": cast(self.similarity_type, int),
            "similarity_hash": self.similarity_hash,
        }

    def get_ref(self):
        return "-".join(sorted([self.img_1, self.img_2]))
