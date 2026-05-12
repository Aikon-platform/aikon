import json
from typing import Tuple, List, Literal, Dict

from app.config.settings import (
    CANTALOUPE_APP_URL,
)
from app.webapp.models.digitization import Digitization
from app.webapp.models.region_extraction import RegionExtraction

from app.webapp.utils.logger import log
from app.webapp.utils.paths import REGIONS_PATH


def get_file_region_extraction(
    region_extraction: RegionExtraction,
) -> Tuple[List[str], Literal["txt"]] | Tuple[List[Dict], Literal["json"]] | Tuple[
    None, None
]:
    json_file = REGIONS_PATH / f"{region_extraction.get_ref()}.json"
    if json_file.exists():
        try:
            with open(json_file, "rb") as f:
                return json.load(f), "json"
        except Exception:
            return None, None

    txt_file = REGIONS_PATH / f"{region_extraction.get_ref()}.txt"
    if txt_file.exists():
        try:
            with open(txt_file, "r") as f:
                return [line.strip() for line in f.readlines()], "txt"
        except Exception:
            return None, None
    log(f"[get_file_region_extraction] Neither {json_file} nor {txt_file} exists")
    return None, None


def get_region_extraction_img(region_extraction: RegionExtraction):
    data, anno_format = get_file_region_extraction(region_extraction)
    if data is None:
        return []

    imgs = []
    img_name = f"{region_extraction.get_ref()}_0000.jpg"
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


def create_empty_region_extraction(digit: Digitization) -> RegionExtraction:
    from app.webapp.utils.iiif.annotation import index_manifest

    imgs = digit.get_imgs()
    if len(imgs) == 0:
        log(
            f"[create_empty_region_extraction] Digit #{digit.id} has no images",
        )
        return False

    try:
        region_extraction = RegionExtraction.objects.create(
            digitization=digit, model="Manual"
        )
    except Exception as e:
        log(
            f"[create_empty_region_extraction] Unable to create new RegionExtraction for digit #{digit.id} in the database",
            e,
        )
        return False

    with open(f"{REGIONS_PATH}/{region_extraction.get_ref()}.json", "w") as _:
        # TODO check if necessary
        pass

    try:
        success = index_manifest(region_extraction.get_manifest_url())
        if not success:
            log(
                f"[create_empty_region_extraction] unable to index manifest in SAS for RegionExtraction #{region_extraction.id}."
                f"Deleting RegionExtraction record.",
            )
            region_extraction.delete()
            return False
    except Exception as e:
        log(
            f"[create_empty_region_extraction] Error when indexing manifest in SAS for RegionExtraction #{region_extraction.id}."
            f"Deleting RegionExtraction record.",
            e,
        )
        region_extraction.delete()
        return False

    return region_extraction
