from glob import glob

from vhsapp.utils.logger import iiif_log, console, log
from vhsapp.utils.paths import MEDIA_PATH, IMG_PATH, BASE_DIR


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
