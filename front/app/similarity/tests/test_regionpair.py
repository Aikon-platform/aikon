# NOTE `admin` postgres user needs persmission to create and drop a database
# if you get an error when running tests, do:
# >>> sudo -u postgres psql        # bash login to psql as postgres
# >>> ALTER USER admin CREATEDB;   # grant db creation privileges to user admin.


import csv
import ast
import json
import pathlib
from typing import Literal
from datetime import datetime
from collections.abc import Callable

from django.db.models import Q
from django.urls import reverse
from django.test import TestCase, Client

from ..models.region_pair import RegionPair
from ...config.settings.base import APP_NAME
from ...webapp.utils.functions import sort_key

DATA_FILE = pathlib.Path(__file__).parent.resolve() / "data_regionpair.csv"

with open(DATA_FILE, mode="r") as fh:
    reader = csv.reader(fh, delimiter=",", quotechar='"')
    HEADERS = next(reader)
    DATA = [row for row in reader]


# take the CSV file and process it so that it can be saved to database
def clean_data(data: list[str]) -> dict:
    def row_to_obj(row: list) -> dict:
        return {h: r for (h, r) in zip(HEADERS, row)}

    data = [row_to_obj(row) for row in DATA]
    for row in data:
        for k in ["regions_id_1", "regions_id_2", "category", "similarity_type"]:
            row[k] = int(row[k]) if len(row[k]) else None
        for k in ["created_at", "updated_at"]:
            row[k] = (
                datetime.strptime(row[k], r"%Y/%m/%d %H:%M:%S") if len(row[k]) else None
            )
        row["score"] = float(row["score"]) if len(row["score"]) else None
        row["is_manual"] = True if row["is_manual"] == "t" else False
        row["category_x"] = (
            [int(x) for x in set(ast.literal_eval(row["category_x"]))]
            if len(row["category_x"])
            else []
        )
    return data


def get_cat(pk) -> int:
    ...


class RegionPairTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        data = clean_data(DATA)
        # TODO cascade to copy related tables (by hand or programatically)
        # RegionPair => Region => Digitization // nullable fields : => Witness => Place
        #                                      // nullable fields : => Source
        print(
            set(
                [row["regions_id_1"] for row in data]
                + [row["regions_id_2"] for row in data]
            )
        )
        for row in data:
            RegionPair.objects.create(**row)

    @staticmethod
    def getcount():
        return RegionPair.objects.count()

    @staticmethod
    def getcat(pk) -> int:
        """
        :raises: DoesNotExist if `pk` is not found in `RegionPair`
        """
        return RegionPair.objects.get(pk=pk).category

    def get_row_and_assert(self, img_tuple: tuple[str, str]) -> RegionPair:
        """
        img_tuple is a tuple of (img_1, img_2). assert there's only 1 row matching this tuple and return it
        """
        img_1, img_2 = img_tuple
        matches = RegionPair.objects.filter(
            # we do bidirectionnal query instead of using sort_key to ensure there's only 1 row matching img_tuple
            (Q(img_1=img_1) & Q(img_2=img_2))
            | (Q(img_1=img_2) & Q(img_1=img_1))
        )
        self.assertEqual(matches.count(), 1)
        return matches.first()

    def assert_create_or_update(
        self,
        method: Literal["get", "post"],  # http method
        operation: Literal[
            "create", "update"
        ],  # the type of operation. if "create", a new row is created, otherwise it's updated. modifies the types of tests being run.
        request_kwargs: dict[str | int],  # parameters of the django client query
        # category_expected: int,                  # the new category that should have been updated
        img_tuple: tuple[
            str, str
        ],  # tuple of (img_1, img_2) to fetch the created or updated row
    ):
        """
        abstract function to test different types of regionpair creations and updates
        """
        request_func = self.client.get if method == "get" else self.client.post
        rowcount_pre_update = self.getcount()

        r = request_func(**request_kwargs)

        rowcount_post_update = self.getcount()
        assert_rowcount = (
            self.assertEqual if operation == "update" else self.assertNotEqual
        )
        self.assertEqual(r.status_code, 200)
        assert_rowcount(rowcount_pre_update, rowcount_post_update)
        row_post_update = self.get_row_and_assert(img_tuple=img_tuple)

        return row_post_update

    def test_sort_key(self):
        a = "wit76_pdf76_0319_628,2234,455,191.jpg"
        b = "wit247_man247_0141_1114,1459,249,300.jpg"
        c = "wit247_man0001_0141_1114,1459,249,300.jpg"
        l1 = [a, b]
        l2 = [b, a]
        l3 = [c, a, b]
        l1_sorted = sorted(l1, key=sort_key)
        l2_sorted = sorted(l2, key=sort_key)
        l3_sorted = sorted(l3, key=sort_key)
        self.assertEqual(l1_sorted[1], b)
        self.assertEqual(l2_sorted[0], a)
        self.assertEqual(l1_sorted, l2_sorted)
        self.assertEqual(l3_sorted, [a, c, b])

    def test_save_category(self):
        """
        test similarity.views.save_category

        we take the first regionpair row and request to save a swapped version of it: (img_1,img_2) is in the db, we save (img_2,img_1).
        assert that the existing row is updated (and that a new row is not created)
        """
        rp = RegionPair.objects.first()
        rp_id = rp.id
        img_tuple = (rp.img_1, rp.img_2)

        cat = 3  # meow
        payload = rp.get_dict()
        # request to save the swapped version of rp, that aldready exists in the database. this should lead in just updating rp.
        payload["img_1"] = img_tuple[1]
        payload["img_2"] = img_tuple[0]
        payload["category"] = cat
        request_kwargs = {
            "path": reverse("similarity:save-category"),
            "content_type": "application/json",
            "data": payload,
        }
        rp_post_update = self.assert_create_or_update(
            "post", "update", request_kwargs, img_tuple
        )
        self.assertEqual(cat, self.getcat(pk=rp_post_update.id))

    def test_add_region_pair(self):
        """
        test similarity.views.add_region_pair
        """
        # example payload : {'q_img': 'wit3_pdf8_01_122,286,220,1128', 's_img': 'wit3_pdf8_01_1363,299,202,1111', 'similarity_type': 2}

        # test 1: update an existing row (we run 2 tests, one where img_tuple is swapped and one where it isn't)
        rp = RegionPair.objects.first()
        for img_tuple in [(rp.img_1, rp.img_2), (rp.img_2, rp.img_1)]:
            img_tuple = tuple(
                img.replace(".jpg", "") for img in img_tuple
            )  # strip extension
            payload = {
                "q_img": img_tuple[0],
                "s_img": img_tuple[1],
                "similarity_type": 2,
            }
            request_kwargs = {
                "path": reverse(
                    "similarity:add-witness-region-pair", kwargs={"wid": 1}
                ),
                "content_type": "application/json",
                "data": payload,
            }
            rp_post_update = self.assert_create_or_update(
                "post", "update", request_kwargs, img_tuple
            )
            self.assertEqual(rp_post_update.is_manual, True)
            self.assertEqual(rp_post_update.similarity_type, True)

        # test 2: create a new row

        # test 3: expected failure

    def test_process_similarity_file(self):
        # TODO
        pass

    def tearDown(self):
        """"""
