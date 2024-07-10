import re

from app.config.settings import (
    CANTALOUPE_APP_URL,
)
from app.webapp.models.digitization import Digitization
from app.webapp.models.regions import Regions
from app.webapp.utils.constants import MANIFEST_V2

from app.webapp.utils.logger import log
from app.webapp.utils.paths import REGIONS_PATH


def get_txt_regions(regions: Regions):
    try:
        with open(f"{REGIONS_PATH}/{regions.get_ref()}.txt") as f:
            return [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        return None


def get_regions_img(regions: Regions):
    lines = get_txt_regions(regions)
    if lines is None:
        return []

    imgs = []
    img_name = f"{regions.get_ref()}_0000.jpg"
    for line in lines:
        if len(line.split()) == 2:
            img_name = line.split()[1]
        else:
            x, y, w, h = line.split()
            imgs.append(
                f"{CANTALOUPE_APP_URL}/iiif/2/{img_name}/{x},{y},{w},{h}/full/0/default.jpg"
            )
    return imgs


def create_empty_regions(digit: Digitization):
    from app.webapp.utils.iiif.annotation import index_manifest_in_sas

    imgs = digit.get_imgs()
    if len(imgs) == 0:
        log(
            f"[create_empty_regions] Digit #{digit.id} has no images",
        )
        return False

    try:
        regions = Regions(digitization=digit, model="Manual")
        regions.save()
    except Exception as e:
        log(
            f"[create_empty_regions] Unable to create new Regions for digit #{digit.id} in the database",
            e,
        )
        return False

    try:
        with open(f"{REGIONS_PATH}/{regions.get_ref()}.txt", "w") as regions_file:
            for i, img_name in enumerate(imgs, 1):
                regions_file.write(f"{i} {img_name}\n")
            # TODO check if necessary
    except Exception as e:
        log(
            f"[create_empty_regions] unable to create new Regions file for digit #{digit.id}",
            e,
        )
        return False

    try:
        # TODO some weird inconsistent problem with SAS (fails here unpredictably)
        success = index_manifest_in_sas(regions.gen_manifest_url(version=MANIFEST_V2))
        if not success:
            log(
                f"[create_empty_regions] unable to index manifest in SAS for Regions #{regions.id}",
            )
            # TODO delete region record if not success?
            return False
    except Exception as e:
        log(
            f"[create_empty_regions] unable to index manifest in SAS for Regions #{regions.id}",
            e,
        )
        return False

    return regions


def check_regions_file(file_content):
    # Either contains a number then an img.jpg / Or a series of 4 numbers
    pattern = re.compile(r"^\d+\s+\S+\.jpg$|^\d+\s\d+\s\d+\s\d+$")
    for line in file_content.split("\n"):
        if line == "":
            continue
        if not pattern.match(line):
            log(f"[check_regions_file] incorrect line {line}")
            return False
    return True
