# NOTE `admin` postgres user needs persmission to create and drop a database
# if you get an error when running tests, do:
# >>> sudo -u postgres psql        # bash login to psql as postgres
# >>> ALTER USER admin CREATEDB;   # grant db creation privileges to user admin.


import csv
import ast
import pathlib
from datetime import datetime
from typing import List, Dict

from django.test import TestCase, Client

from ..models.region_pair import RegionPair
from ...webapp.utils.functions import sort_key

DATA_FILE = pathlib.Path(__file__).parent.resolve() / "data_regionpair.csv"

with open(DATA_FILE, mode="r") as fh:
    reader = csv.reader(fh, delimiter=",", quotechar='"')
    HEADERS = next(reader)
    DATA = [row for row in reader]


def clean_data(data: List) -> Dict:
    def row_to_obj(row: List) -> Dict:
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


class RegionPairTestCase(TestCase):
    def setUp(self):
        self.c = Client()
        data = clean_data(DATA)
        for row in data:
            RegionPair.objects.create(**row)

    def test_sort_key(self):
        a = "wit76_pdf76_0319_628,2234,455,191.jpg"
        b = "wit247_man247_0141_1114,1459,249,300.jpg"
        c = "wit247_man01_0141_1114,1459,249,300.jpg"
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

    def tearDown(self):
        """"""
