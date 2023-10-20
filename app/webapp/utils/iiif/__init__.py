import re

from app.webapp.utils.logger import iiif_log, console, log
from app.config.settings import CANTALOUPE_APP_URL, APP_URL, APP_NAME

IIIF_ICON = "<img alt='IIIF' src='https://iiif.io/assets/images/logos/logo-sm.png' height='15'/>"


def get_id(dic):
    if isinstance(dic, list):
        dic = dic[0]

    if isinstance(dic, dict):
        try:
            return dic["@id"]
        except KeyError:
            try:
                return dic["id"]
            except KeyError as e:
                log(f"[get_id] No id provided {e}")

    if isinstance(dic, str):
        return dic

    return None


def get_height(img_rsrc):
    try:
        img_height = img_rsrc["height"]
    except KeyError:
        return None
    return int(img_height)


def get_width(img_rsrc):
    try:
        img_width = img_rsrc["width"]
    except KeyError:
        return None
    return int(img_width)


def gen_iiif_url(
    img,
    vers=2,
    res="full/full/0",
    color="default",
    ext="jpg",
):
    # E.g. "http://localhost/iiif/2/image_name.jpg/full/full/0/default.jpg"
    # return f"{scheme}://{host}{f':{port}' if port else ''}/iiif/{vers}/{img}/{res}/{color}.{ext}"
    return f"{CANTALOUPE_APP_URL}/iiif/{vers}/{img}/{res}/{color}.{ext}"


def parse_ref(record_ref):
    # wit_ref = {wit_abbr}{wit_id}
    # digit_ref = {wit_abbr}{wit_id}_{digit_abbr}{digit_id}
    # anno_ref = {wit_abbr}{wit_id}_{digit_abbr}{digit_id}_anno{anno_id}

    wit_pattern = r"(?P<wit_abbr>[a-zA-Z]+)(?P<wit_id>\d+)"
    digit_pattern = r"(?P<digit_abbr>[a-zA-Z]+)(?P<digit_id>\d+)"
    anno_pattern = r"anno(?P<anno_id>\d+)"

    wit_ref_pattern = f"{wit_pattern}"
    digit_ref_pattern = f"{wit_pattern}_{digit_pattern}"
    anno_ref_pattern = f"{digit_ref_pattern}_{anno_pattern}"

    wit_match = re.match(wit_ref_pattern, record_ref)
    digit_match = re.match(digit_ref_pattern, record_ref)
    anno_match = re.match(anno_ref_pattern, record_ref)

    if anno_match:
        return {
            "wit": (wit_match.group("wit_abbr"), int(wit_match.group("wit_id"))),
            "digit": (
                digit_match.group("digit_abbr"),
                int(digit_match.group("digit_id")),
            ),
            "anno": ("anno", int(anno_match.group("anno_id"))),
        }
    elif digit_match:
        return {
            "wit": (wit_match.group("wit_abbr"), int(wit_match.group("wit_id"))),
            "digit": (
                digit_match.group("digit_abbr"),
                int(digit_match.group("digit_id")),
            ),
            "anno": None,
        }
    elif wit_match:
        return {
            "wit": (wit_match.group("wit_abbr"), int(wit_match.group("wit_id"))),
            "digit": None,
            "anno": None,
        }
    return None
