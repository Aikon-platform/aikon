import re

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from app.webapp.utils.functions import normalize_str, substrs_in_str
from app.webapp.utils.logger import iiif_log, console, log
from app.config.settings import CANTALOUPE_APP_URL, APP_URL, APP_NAME

IIIF_ICON = "<img alt='IIIF' src='/static/img/logo-iiif.png' height='15'/>"
NO_LICENSE = f"{APP_URL}/{APP_NAME}/rgpd#license"


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

    wit_pattern = r"(?P<wit_abbr>[a-zA-Z]+)(?P<wit_id>\d+)"  # TODO: remplacer par wit
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


def get_version_nb(lic):
    version = re.findall(r"\d\.\d", lic)
    if len(version):
        return version[0]
    nb = re.findall(r"\d", lic)
    if len(nb):
        return f"{nb[0]}.0"
    return "1.0"


def get_license_url(lic):
    # TODO improve
    validator = URLValidator()
    try:
        validator(lic)
    except ValidationError as e:
        lic = normalize_str(lic).replace(" ", "")
        version = get_version_nb(lic)
        if substrs_in_str(lic, ["publicdomain", "cc0", "pdm"]):
            return "https://creativecommons.org/publicdomain/mark/1.0/"
        if substrs_in_str(lic, ["byncsa", "noncommercialsharealike"]):
            return f"https://creativecommons.org/licenses/by-nc-sa/{version}/"
        if substrs_in_str(lic, ["byncnd", "noncommercialnoderiv"]):
            return f"https://creativecommons.org/licenses/by-nc-nd/{version}/"
        if substrs_in_str(lic, ["bysa", "sharealike"]):
            return f"https://creativecommons.org/licenses/by-sa/{version}/"
        if substrs_in_str(lic, ["bync", "noncommercial"]):
            return f"https://creativecommons.org/licenses/by-nc/{version}/"
        if substrs_in_str(lic, ["bynd", "noderiv"]):
            return f"https://creativecommons.org/licenses/by-nd/{version}/"
        if substrs_in_str(lic, ["by"]):
            return f"https://creativecommons.org/licenses/by/{version}/"
        return NO_LICENSE
    return lic
