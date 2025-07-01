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

    def get_row_and_assert(self, img_tuple: tuple[str, str]) -> RegionPair:
        """
        img_tuple is a tuple of (img_1, img_2). assert there's only 1 row matching this tuple and return it
        """
        img_1, img_2 = img_tuple
        matches = RegionPair.objects.filter(
            # we do bidirectionnal query instead of using sort_key to ensure there's only 1 row matching img_tuple
            (Q(img_1=img_1) & Q(img_2=img_2))
            | (Q(img_1=img_2) & Q(img_2=img_1))  # pyright: ignore
        )
        self.assertEqual(matches.count(), 1)
        return matches.first()

    def assert_create_or_update(
        self,
        method: Literal["get", "post"],
        operation: Literal["create", "update", "delete"],
        request_kwargs: dict,
        img_tuple: tuple[str, str],
    ):
        """
        abstract function to test different types of regionpair creations and updates

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

        row_post_update = self.get_row_and_assert(img_tuple)
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
        # function concentrating a single query and all its tests
        def do_query(
            img_tuple_noext: tuple[str, str],  # no extension !
            wid: int,
            rid: int,
            operation: Literal["create", "update"],
        ) -> None:
            img_tuple_withext = tuple(f"{i}.jpg" for i in img_tuple_noext)
            # example payload : {'q_img': 'wit3_pdf8_01_122,286,220,1128', 's_img': 'wit3_pdf8_01_1363,299,202,1111', 'similarity_type': 2}
            payload = {
                "q_img": img_tuple_noext[0],
                "s_img": img_tuple_noext[1],
                "similarity_type": 2,
            }
            request_kwargs = {
                "path": reverse(
                    "similarity:add-region-pair", kwargs={"wid": wid, "rid": rid}
                ),
                "content_type": "application/json",
                "data": payload,
            }
            rp_post_update = self.assert_create_or_update(
                "post", operation, request_kwargs, img_tuple_withext  # pyright: ignore
            )
            self.assertEqual(rp_post_update.is_manual, True)
            self.assertEqual(rp_post_update.similarity_type, 2)
            return

        # test 1: update an existing row (we run 2 tests, one where img_tuple is swapped and one where it isn't)
        rp = RegionPair.objects.first()
        for img_tuple, rid in [
            ((rp.img_1, rp.img_2), rp.regions_id_1),
            ((rp.img_2, rp.img_1), rp.regions_id_2),
        ]:
            # add-region-pair expects image ids without file extension
            img_tuple = tuple(img.replace(".jpg", "") for img in img_tuple)
            wid = int(re.search(r"^wit(\d+)", img_tuple[0])[1])  # pyright: ignore
            do_query(img_tuple, wid, rid, "update")

        # test 2: create a new row
        # to create a new row, we must select a tuple (img_1, img_2) that is not in the database. we select img_1 from the 1st row in RegionPair and then selecting img_2 from a row that has no comparison to img_1
        rp_1 = RegionPair.objects.order_by("id").first()
        # all rows with a relation to rp_1.img_1
        rels_to_rp_1 = RegionPair.objects.values_list("id").filter(
            Q(img_1=rp_1.img_1) | Q(img_2=rp_1.img_1)
        )
        rp_2 = (
            RegionPair.objects.filter(~Q(id__in=rels_to_rp_1))
            .order_by("id")
            .reverse()[0]
        )
        img_1 = rp_1.img_1
        img_2 = rp_2.img_2
        rid_1 = rp_1.regions_id_1
        wid_1 = int(re.search(r"^wit(\d+)", img_1)[1])  # pyright: ignore

        # assert that (img_1, img_2) does not exist in the db
        self.assertEqual(
            RegionPair.objects.filter(
                (Q(img_1=img_1) & Q(img_2=img_2))  # pyright: ignore
                | (Q(img_1=img_2) & Q(img_2=img_1))
            ).count(),
            0,
        )

        # test that row creation works
        img_tuple = tuple(img.replace(".jpg", "") for img in (img_1, img_2))
        do_query(img_tuple, wid_1, rid_1, "create")

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

        # cleanup: delete test files
        finally:
            score_file_path.unlink()
            score_file_path.parent.resolve().rmdir()
        return
