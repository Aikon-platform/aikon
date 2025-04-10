# check which packages are installed and which packages are missing in the current virualenv

import pkg_resources
import argparse
import os
import re

from typing import List
from pkg_resources import DistributionNotFound, VersionConflict

FP = os.path.abspath(__file__)  # directory of the current file
SCRIPTS_DIR = os.path.abspath(os.path.dirname(__file__))
FRONT_DIR = os.path.abspath(os.path.join(SCRIPTS_DIR, ".."))
APP_DIR = os.path.abspath(os.path.join(FRONT_DIR, "app"))


def requirements_file_parser(
    requirements_path=str | os.PathLike, requirements: List[str | None] = []
) -> List[str]:
    """
    parse a requirements file. this is a very simplified parser: lines can only
    - be empty
    - contain a path to another requirements file (line starts with `-r`)
    - contain comments (line starts with `#`)
    """
    contents: str = ""
    with open(requirements_path, mode="r") as fh:
        contents = fh.read()
    for line in contents.split("\n"):
        line = line.strip()
        if not len(line) or line.startswith("#"):
            pass
        elif line.startswith("-r"):
            new_requirements_path = re.sub("^-r\s+", "", line)
            new_requirements_path = os.path.join(
                os.path.dirname(requirements_path), new_requirements_path
            )
            requirements = requirements_file_parser(new_requirements_path, requirements)
        else:
            requirements.append(line)
    return requirements


def get_issues(reqfile: str | os.PathLike) -> None:
    """
    print all installation errors in the terminal
    """
    requirements = requirements_file_parser(reqfile)

    count = 0
    print("")
    print("💡 searching for requirements issues...")
    for req in requirements:
        try:
            pkg_resources.require(req)
        except VersionConflict as e:
            count += 1
            req = pkg_resources.Requirement(req)
            installed = pkg_resources.get_distribution(req.name)
            print(f"❕ version conflict: expected {req}, installed {installed} ")
        except DistributionNotFound as e:
            count += 1
            print(f"❗ distribution not found: {pkg_resources.Requirement(req)}")
    if count:
        print(f"💔 {count} errors found !")
    else:
        print(f"✨ no errors found !")
    return


def get_file(fp: str) -> os.PathLike:
    fp = os.path.abspath(fp)
    if not os.path.isfile(fp):
        raise FileNotFoundError(
            f"\n\t>>> requirements file not found: {fp}\n\t>>> exiting..."
        )
    return fp


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "get_package_issues",
        description="find packages in a requirements file missing from your current venv or with a dependency conflict",
    )
    parser.add_argument(
        "-f",
        "--file",
        required=True,
        help="the requirements file you want to test",
    )
    args = parser.parse_args()
    reqfile = get_file(args.file)
    get_issues(reqfile)
