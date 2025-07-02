r"""
test the writing/updating of RegionPair objects.

the process is somewhat convoluted since we need to use a replication of a database to work with:
- read the csv files in `TBL_TO_CSV` as pandas dfs
- clean and retype them. mostly, we empty optional foreign keys to avoid having to replicate tons of tables
- populate the database using psql's `\copy` (native postgres COPY demands rights and other weird things, so we use psql as a subprocess instead: it doesn't require the same authorizations)
- run the tests (finally !)
"""

# NOTE `admin` postgres user needs persmission to create and drop a database
# if you get an error when running tests, do:
# >>> sudo -u postgres psql        # bash login to psql as postgres
# >>> ALTER USER admin CREATEDB;   # grant db creation privileges to user admin.

import re
import random
from typing import Literal

from django.db.models import Q
from django.urls import reverse
from django.test import TestCase, Client

from ..utils import score_file_to_db
from ..models.region_pair import RegionPair
from ...webapp.utils.functions import sort_key
from .helpers import (
    clean_data,
    psql_cmd_copy,
    run_subprocess,
    create_user,
    fix_id_autoincrement,
    generate_score_file,
)


class RegionPairTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        """populate the db. runs only 1 time for the whole test case, instead of `setUp` which runs once per test"""

        tbl_list = [
            "webapp_digitization",
            "webapp_regions",
            "webapp_regionpair",
            "webapp_witness",
        ]
        user_id = create_user()
        tbl_to_csv_local = clean_data(
            tbl_list,
            user_id,  # pyright:ignore
        )

        for (tblname, csvfile) in tbl_to_csv_local:
            cmd = psql_cmd_copy(tblname, csvfile)
            run_subprocess(cmd)
        fix_id_autoincrement(tbl_list)

    def setUp(self):
        self.client = Client()

    def tearDown(self):
        """"""

    @staticmethod
    def getcount():
        return RegionPair.objects.count()

    @staticmethod
    def getcat(pk) -> int:
        """
        :raises: DoesNotExist if `pk` is not found in `RegionPair`
        """
        return RegionPair.objects.get(pk=pk).category

    def get_row_and_assert(
        self, img_tuple: tuple[str, str], row_exists=True
    ) -> RegionPair | None:
        """
        img_tuple is a tuple of (img_1, img_2).
        - if `row_exists`, assert there's only 1 row matching this tuple and return it
        - else, assert no rows match this tuple
        """
        img_1, img_2 = img_tuple
        matches = RegionPair.objects.filter(
            # we do bidirectionnal query instead of using sort_key to ensure there's only 1 row matching img_tuple
            (Q(img_1=img_1) & Q(img_2=img_2))
            | (Q(img_1=img_2) & Q(img_2=img_1))  # pyright: ignore
        )
        if row_exists:
            self.assertEqual(matches.count(), 1)
            return matches.first()
        else:
            self.assertEqual(matches.count(), 0)
            return None

    def save_category_kwargs(self, payload):
        return {
            "path": reverse("similarity:save-category"),
            "content_type": "application/json",
            "data": payload,
        }

    def assert_extensions(self):
        """all RegionPair.(img_1|img_2) must finish with .jpg"""
        self.assertEqual(
            RegionPair.objects.filter(
                Q(img_1__endswith=".jpg") | Q(img_2__endswith=".jpg")
            ).count(),
            RegionPair.objects.count(),
        )
        return

    def assert_modifs(
        self,
        method: Literal["get", "post"],
        operation: Literal["create", "update", "delete"],
        request_kwargs: dict,
        img_tuple: tuple[str, str],
    ) -> RegionPair | None:
        """
        abstract function to test different types of regionpair create, update and delete

        :param method: http method
        :param operation: the type of operation. if "create", a new row is created, otherwise it's updated. modifies the types of tests being run
        :param request kwargs: parameters of the django client query
        :param img_tuple: tuple of (img_1, img_2) used to fetch the created or updated row
        """
        request_func = self.client.get if method == "get" else self.client.post

        rowcount_pre_update = self.getcount()
        r = request_func(**request_kwargs)
        rowcount_post_update = self.getcount()

        self.assertEqual(r.status_code, 200)  # pyright: ignore
        comp = (
            rowcount_pre_update < rowcount_post_update
            if operation == "create"
            else rowcount_pre_update == rowcount_post_update
            if operation == "update"
            else rowcount_pre_update > rowcount_post_update
        )
        self.assertTrue(comp)

        if operation != "delete":
            row_post_update = self.get_row_and_assert(img_tuple, True)
            return row_post_update
        else:
            self.get_row_and_assert(img_tuple, False)
            return

    def assert_save_category(
        self, payload, operation=["create", "update", "delete"]
    ) -> RegionPair | None:
        """
        abstract function to test similarity.views.save_category
        """
        cat = payload["category"]
        img_tuple = (payload["img_1"], payload["img_2"])
        request_kwargs = self.save_category_kwargs(payload)
        rp_post_update = self.assert_modifs(
            "post", operation, request_kwargs, img_tuple
        )

        if operation != "delete":
            self.assertEqual(cat, self.getcat(pk=rp_post_update.id))
        return rp_post_update

    def get_new_regionpair(self) -> tuple[tuple[str, int, int], tuple[str, int, int]]:
        """
        to create a new row, we must select a tuple (img_1, img_2) that is not in the database.
        we select img_1 from a random RegionPair row and then selecting img_2 from a row that has no comparison to img_1
        """
        get_wid = lambda img_id: int(
            re.search(r"^wit(\d+)", img_id)[1]  # pyright: ignore
        )

        choices = RegionPair.objects.values_list("id", flat=True)
        rp_1 = RegionPair.objects.get(id=random.choice(choices))
        img_1 = rp_1.img_1
        rid_1 = rp_1.regions_id_1
        wid_1 = get_wid(img_1)

        # all rows with a relation to `img_1`
        rels_to_rp_1 = RegionPair.objects.values_list("id").filter(
            Q(img_1=rp_1.img_1) | Q(img_2=rp_1.img_1)
        )

        rp_2 = RegionPair.objects.filter(~Q(id__in=rels_to_rp_1)).order_by("id").first()
        img_2 = rp_2.img_2
        rid_2 = rp_2.regions_id_2
        wid_2 = get_wid(img_2)

        # assert that (img_1, img_2) does not exist in the db
        self.assertEqual(
            RegionPair.objects.filter(
                (Q(img_1=img_1) & Q(img_2=img_2))  # pyright: ignore
                | (Q(img_1=img_2) & Q(img_2=img_1))
            ).count(),
            0,
        )
        return (img_1, rid_1, wid_1), (img_2, rid_2, wid_2)

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
        return

    def test_save_category(self):
        """
        test similarity.views.save_category (not for propagations)

        we take the first regionpair row and request to save a swapped version of it: (img_1,img_2) is in the db, we save (img_2,img_1).
        assert that the existing row is updated (and that a new row is not created)
        """
        rp = RegionPair.objects.first()
        img_tuple = (rp.img_1, rp.img_2)

        cat = 3  # meow
        payload = rp.get_dict()
        # request to save the swapped version of rp, that aldready exists in the database. this should lead in just updating rp.
        payload["img_1"] = img_tuple[1]
        payload["img_2"] = img_tuple[0]
        payload["category"] = cat
        self.assert_save_category(payload, "update")
        self.assert_extensions()
        return

    def test_save_category_propagation(self):
        """
        test similarity.views.save_category for propagations.

        expected behaviour:
        - if the propagation does not exist in the database and the user annotates it, add the row to the db and update the category
        - if the propagation exists in the db, is annotated and the user removes the annotation, delete the row from the db
        """
        (img_1, rid_1, wid_1), (img_2, rid_2, _) = self.get_new_regionpair()

        # test 1: add the new pair to the db by setting its `RegionPair.category`
        # `rp` has the same defaults as what is sent by `get_propagated_matches`, expect that `category=1`: `rp` has been annotated by the user
        rp_dict = RegionPair(
            img_1=img_1,
            img_2=img_2,
            regions_id_1=rid_1,
            regions_id_2=rid_2,
            score=None,
            is_manual=False,
            similarity_type=3,  # it's a propagation
            category_x=[],
            category=1,
        ).get_dict()
        rp = self.assert_save_category(rp_dict, "create")
        self.assertEqual(rp.category, 1)

        # test 2: update the pair added in test 1 by setting a new category
        rp.category = 3
        rp = self.assert_save_category(rp.get_dict(), "update")
        self.assertEqual(rp.category, 3)

        # test 3: remove the pair by unsetting its `RegionPair.category`
        # setting the category as None is expected to delete the row
        rp.category = None  # pyright: ignore
        self.assert_save_category(rp.get_dict(), "delete")

        self.assert_extensions()
        return

    def test_add_region_pair(self):
        """
        test similarity.views.add_region_pair
        """
        # function concentrating a single query and all its tests
        def do_query(
            img_tuple: tuple[str, str],  # with extension !
            wid: int,
            rid: int,
            operation: Literal["create", "update"],
        ) -> None:
            # example payload : {'q_img': 'wit3_pdf8_01_122,286,220,1128', 's_img': 'wit3_pdf8_01_1363,299,202,1111', 'similarity_type': 2}
            payload = {
                "q_img": img_tuple[0].replace(".jpg", ""),
                "s_img": img_tuple[1].replace(".jpg", ""),
                "similarity_type": 2,
            }
            request_kwargs = {
                "path": reverse(
                    "similarity:add-region-pair", kwargs={"wid": wid, "rid": rid}
                ),
                "content_type": "application/json",
                "data": payload,
            }
            rp_post_update = self.assert_modifs(
                "post", operation, request_kwargs, img_tuple  # pyright: ignore
            )
            self.assertEqual(rp_post_update.is_manual, True)  # pyright: ignore
            self.assertEqual(rp_post_update.similarity_type, 2)  # pyright: ignore
            return

        # test 1: update an existing row (we run 2 tests, one where img_tuple is swapped and one where it isn't)
        rp = RegionPair.objects.first()
        for img_tuple, rid in [
            ((rp.img_1, rp.img_2), rp.regions_id_1),
            ((rp.img_2, rp.img_1), rp.regions_id_2),
        ]:
            wid = int(re.search(r"^wit(\d+)", img_tuple[0])[1])  # pyright: ignore
            do_query(img_tuple, wid, rid, "update")

        # test 2: create a new row
        (img_1, rid_1, wid_1), (img_2, _, _) = self.get_new_regionpair()
        img_tuple = (img_1, img_2)
        do_query(img_tuple, wid_1, rid_1, "create")  # pyright: ignore
        self.assert_extensions()

        return

    def test_score_file_to_db(self):
        """
        test similarity.utils.score_file_to_db
        """
        score_file_path, (rid_1, rid_2), nb_pairs_written = generate_score_file()

        try:
            rowcount_pre_update = self.getcount()

            # 1: assert number of rows
            score_file_to_db(score_file_path)
            rowcount_post_update = self.getcount()
            self.assertEqual(
                rowcount_post_update - rowcount_pre_update, nb_pairs_written
            )

            # 2: assert sort_key has worked
            pairs_written = RegionPair.objects.values_list("img_1", "img_2").filter(
                (Q(regions_id_1=rid_1) & Q(regions_id_2=rid_2))  # pyright: ignore
                | (Q(regions_id_1=rid_2) & Q(regions_id_2=rid_1))
            )
            self.assertTrue(
                all(
                    list(img_tuple) == sorted(img_tuple, key=sort_key)
                    for img_tuple in pairs_written
                )
            )
            self.assert_extensions()

        # cleanup: delete test files
        finally:
            score_file_path.unlink()
            score_file_path.parent.resolve().rmdir()
        return
