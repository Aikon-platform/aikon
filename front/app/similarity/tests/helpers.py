import os
import pathlib
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

from django.contrib.auth.models import User

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


# def reindex():
#     cmd = PSQL_BASE + '-c "SELECT setval(\'django_content_type_id_seq\', (SELECT MAX(id) FROM django_content_type));"'
#     out = run_subprocess(cmd)
#     print(out)


def fix_id_autoincrement(tbl_list: list[str]) -> None:
    """
    force update the autoincrements on all ID columns in tbl_list tables.

    NOTE this is very convoluted BUT:
    we create rows using PSQL's \copy, which means:
    - data insertion is done outside of Django
    - psql only copies the data into the database, and does not update the ID's autoincrements.
    in turn, when we create new rows after the initial `\copy`, PostgreSQL will start incrementing ids from 1, even if there are aldready rows in the database, causing integrity errors (duplicate IDs).
    => this function fixes the issue by ensuring autoincrements start at MAX(id).
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
