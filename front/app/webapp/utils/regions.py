import json
from pathlib import Path

from app.config.settings import (
    CANTALOUPE_APP_URL,
)
from app.webapp.models.digitization import Digitization
from app.webapp.models.regions import Regions
from app.webapp.utils.constants import MANIFEST_V2

from app.webapp.utils.logger import log
from app.webapp.utils.paths import REGIONS_PATH


def get_file_regions(regions: Regions):
    json_file = REGIONS_PATH / f"{regions.get_ref()}.json"
    if json_file.exists():
        try:
            with open(json_file, "rb") as f:
                return json.load(f), "json"
        except Exception:
            return None, None

    txt_file = REGIONS_PATH / f"{regions.get_ref()}.txt"
    if txt_file.exists():
        try:
            with open(txt_file, "r") as f:
                return [line.strip() for line in f.readlines()], "txt"
        except Exception:
            return None, None
    return None, None


def get_regions_img(regions: Regions):
    data, anno_format = get_file_regions(regions)
    if data is None:
        return []

    imgs = []
    img_name = f"{regions.get_ref()}_0000.jpg"
    if anno_format == "txt":
        for line in data:
            if len(line.split()) == 2:
                img_name = line.split()[1]
            else:
                x, y, w, h = line.split()
                imgs.append(
                    f"{CANTALOUPE_APP_URL}/iiif/2/{img_name}/{x},{y},{w},{h}/full/0/default.jpg"
                )
    elif anno_format == "json":
        for annotation in data:  # Iterate through all annotations
            img_name = annotation["source"]
            for crop in annotation["crops"]:
                coord = crop["absolute"]
                x, y, w, h = coord["x1"], coord["y1"], coord["width"], coord["height"]
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
        regions = Regions.objects.create(digitization=digit, model="Manual")
    except Exception as e:
        log(
            f"[create_empty_regions] Unable to create new Regions for digit #{digit.id} in the database",
            e,
        )
        return False

    with open(f"{REGIONS_PATH}/{regions.get_ref()}.json", "w") as _:
        pass

    try:
        # TODO some weird inconsistent problem with SAS (fails here unpredictably)
        success = index_manifest_in_sas(regions.gen_manifest_url(version=MANIFEST_V2))
        if not success:
            log(
                f"[create_empty_regions] unable to index manifest in SAS for Regions #{regions.id}."
                f"Deleting Regions record.",
            )
            regions.delete()
            return False
    except Exception as e:
        log(
            f"[create_empty_regions] Error when indexing manifest in SAS for Regions #{regions.id}."
            f"Deleting Regions record.",
            e,
        )
        regions.delete()
        return False

    return regions
