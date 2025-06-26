import os
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd

from ...config.settings.base import DATABASES

# returns the header of sql table `tblname`
psql_cmd_header = lambda tblname: (
    f'PGPASSWORD="{DATABASES["default"]["PASSWORD"]}" \
    psql -U "{DATABASES["default"]["USER"]}" \
         -d "{DATABASES["test"]["NAME"]}" \
         -c "\copy ( SELECT * FROM {tblname} LIMIT 0 ) TO STDOUT WITH (FORMAT CSV, HEADER)"'
)

# populates sql table `tblname` with data from `csvfile`
psql_cmd_copy = lambda tblname, csvfile: (
    f'PGPASSWORD="{DATABASES["default"]["PASSWORD"]}" \
    psql -U "{DATABASES["default"]["USER"]}" \
         -d "{DATABASES["test"]["NAME"]}" \
         -c "\copy {tblname} FROM \'{csvfile}\' WITH (FORMAT CSV, HEADER MATCH)"'
)


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
def clean_data(tbl_to_csv: list[tuple[str, Path]]) -> list[tuple[str, Path]]:
    tbl_to_csv_local = []  # output
    # table name mapped to array of columns to empty
    empty = {"webapp_regions": ["digitization_id"]}
    # table name mapped to column name mapped to type to retype to
    retype = {
        "webapp_regionpair": {"category": "int"},
    }
    for tblname, csvfile in tbl_to_csv:
        # clean the csv (mainly perform type conversions and empty unnecessary foreign keys)
        df = pd.read_csv(csvfile)
        if tblname in empty:
            df[empty[tblname]] = np.nan
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
        out = subprocess.run(cmd, shell=True, check=True, capture_output=True)
        db_header = out.stdout.decode("utf-8").replace(
            "\n", ""
        )  # convert to str + strip the trailing newline
        db_header = db_header.split(",")

        # reorder columns in `df` to match `db_header`
        assert len(df.columns) == len(db_header), set(db_header).difference(df.columns)
        df = df.reindex(columns=db_header)

        # write to file and build tbl_to_csv_local
        fn_out = f"{os.path.basename(csvfile).replace('.csv', '')}_clean.csv"  # webapp_regions.csv => webapp_regions_clean.csv
        dir_out = csvfile.parent.resolve()  # pyright:ignore
        csvfile_out = dir_out / fn_out
        df.to_csv(csvfile_out, sep=",", header=True, index=False, na_rep="")
        tbl_to_csv_local.append((tblname, csvfile_out))

    return tbl_to_csv_local
