from glob import glob

from vhsapp.utils.logger import iiif_log, console, log
from vhsapp.utils.paths import MEDIA_PATH, IMG_PATH, BASE_DIR


IIIF_ICON = "<img alt='IIIF' src='https://iiif.io/assets/images/logos/logo-sm.png' height='15'/>"


def get_id(dic):
    if type(dic) == list:
        dic = dic[0]

    if type(dic) == dict:
        try:
            return dic["@id"]
        except KeyError:
            try:
                return dic["id"]
            except KeyError as e:
                log(f"[Get id] No id provided {e}")

    if type(dic) == str:
        return dic

    return None


def get_height(img_rsrc):
    try:
        img_height = img_rsrc["height"]
    except KeyError:
        return None
    return img_height


def get_width(img_rsrc):
    try:
        img_width = img_rsrc["width"]
    except KeyError:
        return None
    return img_width
