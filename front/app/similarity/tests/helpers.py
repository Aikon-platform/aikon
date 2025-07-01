import re
import os
import json
import random
import pathlib
import subprocess
from pathlib import Path
from itertools import product

import numpy as np
import pandas as pd

from django.db.models import Q
from django.contrib.auth.models import User

from ..models.region_pair import RegionPair
from ...webapp.models.regions import Regions
from ...config.settings.base import DATABASES


FOLDER = pathlib.Path(__file__).parent.resolve()

# NOTE order is important to avoid sql integrity errors !
TBL_TO_CSV = [
    ("webapp_place", FOLDER / "data" / "webapp_place.csv"),
    ("webapp_edition", FOLDER / "data" / "webapp_edition.csv"),
    ("webapp_witness", FOLDER / "data" / "webapp_witness.csv"),
    ("webapp_digitization", FOLDER / "data" / "webapp_digitization.csv"),
    ("webapp_regions", FOLDER / "data" / "webapp_regions.csv"),
    ("webapp_regionpair", FOLDER / "data" / "webapp_regionpair.csv"),
]

# similarity results json file.
SIMILARITY_JSON = {
    "parameters": {
        "algorithm": "cosine",
        "topk": 20,
        "feat_net": "dino_deitsmall16_pretrain",
        "segswap_prefilter": True,
        "segswap_n": 10,
        "raw_transpositions": ["none"],
    },
    "index": {
        "sources": {},  # metadata for regions extraction
        "images": [],  # index of all images + their metadata
        "transpositions": ["none"],
    },
    "pairs": [],  # results
}

PSQL_BASE = f'PGPASSWORD="{DATABASES["default"]["PASSWORD"]}" \
    psql -U "{DATABASES["default"]["USER"]}" \
         -d "{DATABASES["test"]["NAME"]}" '

# returns the header of sql table `tblname`
psql_cmd_header = lambda tblname: (
    PSQL_BASE
    + f'-c "\copy ( SELECT * FROM {tblname} LIMIT 0 ) TO STDOUT WITH (FORMAT CSV, HEADER)"'
)

# populates sql table `tblname` with data from `csvfile`
psql_cmd_copy = lambda tblname, csvfile: (
    PSQL_BASE
    + f"-c \"\copy {tblname} FROM '{csvfile}' WITH (FORMAT CSV, HEADER MATCH)\""
)


def run_subprocess(cmd) -> str:
    try:
        out = subprocess.run(cmd, shell=True, check=True, capture_output=True)
        return out.stdout.decode("utf-8")
    except subprocess.CalledProcessError as e:
        raise Exception(f"ERROR MESSAGE: {e.stderr.decode('utf-8')}")


def create_user() -> int:
    """
    create a user and return its ID. yes, it is necessary to use PSQL: when creating it through Django,
    it appears in Django but PSQL queries to populate the rest of the database cannot access the user for some obscure reason.
    """
    cmd = (
        PSQL_BASE
        + "-c \"INSERT INTO auth_user (password, username, first_name, last_name, email, date_joined, is_superuser, is_staff, is_active) \
           VALUES ('a very safe password', 'janedoe', 'jane', 'doe', 'jane.doe@test.com', '2025-04-16 11:34:21.401134+00', false, false, false); \
           COMMIT;\""
    )
    run_subprocess(cmd)
    return User.objects.filter(email="jane.doe@test.com").first().id


def fix_id_autoincrement(tbl_list: list[str]) -> None:
    """
    force update the autoincrements on all ID columns in tbl_list tables.

    NOTE this is very convoluted BUT:
    we create rows using PSQL's \copy, which means:
    - data insertion is done outside of Django
    - psql only copies the data into the database, and does not update the ID's autoincrements.
    in turn, when we create new rows after the initial `\copy`, PostgreSQL will start incrementing ids from 1, even if there are aldready rows in the database, causing integrity errors (duplicate IDs).
    => this function fixes the issue by ensuring autoincrements start at MAX(id).

    NOTE since IDs are postgreSQL identity columns and not sequences, we can't use Django's built in `sqlsequencereset`: https://docs.djangoproject.com/en/3.1/ref/django-admin/#sqlsequencereset

    see:
    - https://forum.djangoproject.com/t/django-unit-tests-raising-duplicate-key-constraint-errors-on-object-creation/13268
    - https://dba.stackexchange.com/questions/292617/restarting-identity-columns-in-postgresql
    - https://forum.djangoproject.com/t/django-db-utils-integrityerror-duplicate-key-value-violates-unique-key-constraint/15625
    """
    stmt = (
        lambda tblname: f"\"SELECT setval( pg_get_serial_sequence('{tblname}', 'id'), coalesce(MAX(id), 1) ) FROM {tblname};\""
    )
    for tblname in tbl_list:
        cmd = f"{PSQL_BASE} -c {stmt(tblname)}"
        run_subprocess(cmd)
    return


def get_csvfile_from_tblname(
    tblname: str, tbl_to_csv: list[tuple[str, os.PathLike]]
) -> os.PathLike | None:
    for _tblname, _csvfile in tbl_to_csv:
        if tblname == _tblname:
            return _csvfile
    raise ValueError(
        f"invalid table name '{tblname}'. allowed values are {list(t for (t,c) in tbl_to_csv)}"
    )


# load sql exports as dataframes, clean them and write them. returns a copy of `tbl_to_csv` with file paths updates to point to the cleaned files.
def clean_data(tbl_list: list[str], id_user=int) -> list[tuple[str, Path]]:
    # TBL_TO_CSV with only entries that are in tbl_list
    tbl_to_csv_local = [
        (tblname, csvfile) for tblname, csvfile in TBL_TO_CSV if tblname in tbl_list
    ]
    tbl_to_csv_out = []  # output
    # table name mapped to array of columns to empty
    empty = {
        "webapp_digitization": ["source_id"],
        "webapp_witness": ["edition_id", "series_id", "place_id"],
    }
    # fill a column with a default value
    # mostly, django `blank=True` gets translated as `NOT NULL` in SQL, and empty fields in the CSV get translated as by psql's `\copy` as NULL => fill with empty space
    # structure: { "table_name": {"columnname": ["value", True|False]} }
    # if the boolean is True, replace all values in the col. else, replace only empty values
    default = {
        "webapp_digitization": {
            "manifest": [" ", False],
            "images": [" ", False],
            "pdf": [" ", False],
        },
        "webapp_witness": {
            "user_id": [id_user, True],
            "notes": [" ", False],
            "link": [" ", False],
        },
    }
    # table name mapped to column name mapped to type to retype to
    retype = {
        "webapp_regionpair": {"category": "int"},
        "webapp_digitization": {"witness_id": "int"},
        "webapp_witness": {
            "user_id": "int",
            "place_id": "int",
            "volume_nb": "int",
            "nb_pages": "int",
        },
    }
    for tblname, csvfile in tbl_to_csv_local:
        # clean the csv (mainly perform type conversions and empty unnecessary foreign keys)
        df = pd.read_csv(csvfile)
        if tblname in empty:
            df[empty[tblname]] = np.nan
        if tblname in default:
            for col, (val, replace_all) in default[tblname].items():
                df[col] = val if replace_all else df[col].fillna(val)
        if tblname in retype:
            for col, newtype in retype[tblname].items():
                if newtype == "int":
                    df[col] = df[col].astype(
                        "Int64"
                    )  # integer+nan columns in `csvfile` are converted to float by default (since nan is a float) => reconvert them to int
                else:
                    raise NotImplementedError(f"no conversion for {newtype}")

        # load the column names in the test database as a list of strings
        cmd = psql_cmd_header(tblname)
        db_header = run_subprocess(cmd).replace(
            "\n", ""
        )  # convert to str + strip the trailing newline
        db_header = db_header.split(",")

        # reorder columns in `df` to match `db_header`
        assert len(df.columns) == len(
            db_header
        ), f"faulty columns: {set(db_header).difference(df.columns)}"
        df = df.reindex(columns=db_header)

        # mul = 100 * 100
        # df.id = df.id * mul
        # for col in df.columns:
        #     if col.endswith("_id") and col != "user_id":
        #         df[col] = df[col] * mul

        # write to file and build tbl_to_csv_local
        fn_out = f"{os.path.basename(csvfile).replace('.csv', '')}_clean.csv"  # webapp_regions.csv => webapp_regions_clean.csv
        dir_out = csvfile.parent.resolve()  # pyright:ignore
        csvfile_out = dir_out / fn_out
        df.to_csv(csvfile_out, sep=",", header=True, index=False, na_rep="")
        tbl_to_csv_out.append((tblname, csvfile_out))
    return tbl_to_csv_out


def generate_score_file() -> Path:
    """
    generate a score file containing the cartesian product of all images within 2 randomly selected regions extractions

    :returns: the path to the score file.
    """
    out = FOLDER / "data" / "similarity_results.json"
    similarity_json_local = SIMILARITY_JSON

    # 1: find 2 regions that have not been previously compared
    rid_compared_all = RegionPair.objects.values_list(
        "regions_id_1", "regions_id_2"
    ).distinct()

    rid_list = RegionPair.objects.values_list("regions_id_1", flat=True).union(
        RegionPair.objects.values_list("regions_id_2", flat=True)
    )
    rid_1 = None
    not_compared = []  # all regions to which rid_1 has not been compared
    for rid in rid_list:
        compared = set(
            [c[0] for c in rid_compared_all if c[1] == rid]
            + [c[1] for c in rid_compared_all if c[0] == rid]
        )
        not_compared = [
            _rid for _rid in rid_list if _rid not in compared and _rid != rid
        ]
        if len(not_compared):
            rid_1 = rid
            break
    rid_2 = not_compared[random.randint(0, len(not_compared) - 1)]

    # just to be sure that rid_1 and rid_2 have not been compared
    assert (
        RegionPair.objects.filter(
            (Q(regions_id_1=rid_1) & Q(regions_id_2=rid_2))  # pyright: ignore
            | (Q(regions_id_1=rid_2) & Q(regions_id_2=rid_1))
        ).count()
        == 0
    )

    # 2: get all images for rid_1, rid_2 + make a cartesian product of those images. this product will be considered the similarities between img_1_list and img_2_list
    get_img_list = (
        lambda _rid: RegionPair.objects.values_list("img_1", flat=True)
        .filter(regions_id_1=_rid)
        .union(
            RegionPair.objects.values_list("img_2", flat=True).filter(regions_id_2=_rid)
        )
    )
    img_1_list = list(get_img_list(rid_1))
    img_2_list = list(get_img_list(rid_2))

    # assert there are no duplicates in img_1_list and img_2_list (theoretically there are none)
    assert len(img_1_list + img_2_list) == len(set(img_1_list + img_2_list))

    # cartesian product of all images in img_1_list and img_2_list
    rels = list(product(img_1_list, img_2_list))

    # 3: fetch the region's UID (format `wit\d+_(pdf|iiif|zip)\d+_anno\d+`)
    get_regions_uid = lambda _rid: Regions.objects.get(id=_rid).json["ref"]
    regions_uid_1 = get_regions_uid(rid_1)
    regions_uid_2 = get_regions_uid(rid_2)

    # 4: build and write a similarity results file
    make_source = lambda regions_uid: {
        "uid": regions_uid,
        "type": "url_list",
        "src": f"http://example.com/{regions_uid}/list",
        "metadata": {"src": f"http://example.com/{regions_uid}/list"},
    }
    for regions_uid in [regions_uid_1, regions_uid_2]:
        similarity_json_local["index"]["sources"][regions_uid] = make_source(
            regions_uid
        )

    def img_id_to_iiif(img_id):
        img_id = img_id.replace(".jpg", "")
        img_name = (
            re.search(r"^wit\d+_[a-z]+\d+_\d+", img_id)[0] + ".jpg"
        )  # pyright: ignore
        bbox = re.search(r"(\d+,?){4}$", img_id)[0]  # pyright: ignore
        return f"http://example.com/iiif/1/{img_name}/{bbox}/full/0/default.jpg"

    make_image = lambda img_id, regions_uid: {
        "id": img_id.replace(".jpg", ""),
        "src": img_id_to_iiif(img_id),
        "path": f"images/{img_id}",
        "metadata": None,
        "doc_uid": regions_uid,
    }

    for (img_list, regions_uid) in [
        (img_1_list, regions_uid_1),
        (img_2_list, regions_uid_2),
    ]:
        for img_id in img_list:
            similarity_json_local["index"]["images"].append(
                make_image(img_id, regions_uid)
            )

    # replace img_id in rels with index of image in similarity_json_local["index"]["images"]
    def img_id_to_index(img_id):
        img_id_noext = img_id.replace(".jpg", "")
        for idx, img in enumerate(similarity_json_local["index"]["images"]):
            if img["id"] == img_id_noext:
                return idx
        raise ValueError(
            f"could not find {img_id} in `similarity_json_local['index']['images']`"
        )

    for rel in rels:
        rel = tuple(img_id_to_index(img_id) for img_id in rel)
        rel = (
            rel if random.random() < 0.5 else (rel[1], rel[0])
        )  # randomly permutate order of 2 elts in rel
        score = random.random()
        similarity_json_local["pairs"].append([rel[0], rel[1], score, 0, 0])

    with open(out, mode="w") as fh:
        json.dump(similarity_json_local, fh)

    return out
