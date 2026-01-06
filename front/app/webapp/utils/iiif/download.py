import glob
import os
import time
import shutil

import requests
from urllib3.exceptions import ProtocolError
from requests.exceptions import RequestException, Timeout
from PIL import Image, UnidentifiedImageError

from app.webapp.utils.functions import get_json, save_img, sanitize_url
from app.webapp.utils.constants import MAX_SIZE
from app.webapp.utils.paths import IMG_PATH, BASE_DIR, DOWNLOAD_LOG_PATH
from app.webapp.utils.logger import log, download_log
from app.webapp.utils.iiif import get_height, get_width, get_id, get_license_url


def iiif_to_img(manifest_url, digit_ref, digit):
    """
    Extract all images from an IIIF manifest
    """
    from iiif_download import IIIFManifest

    # TODO change config of log fails + do not create img/ folder

    manifest = IIIFManifest(manifest_url, prefix=f"{digit_ref}_")
    manifest.download(save_dir=IMG_PATH)
    digit.add_info(manifest.license)
    return [img.img_path for img in manifest.images]


def save_failed_img(image):
    img_name = image.split(" ")[0]
    img_url = image.split(" ")[1]
    iiif_url = sanitize_url(f"{img_url}/full/full/0/default.jpg")
    time.sleep(20)

    try:
        with requests.get(iiif_url, stream=True) as response:
            response.raw.decode_content = True
            img = Image.open(response.raw)
            save_img(img, img_name)
            # TODO update json property afterwards

    except (RequestException, ProtocolError, Timeout, Exception) as e:
        shutil.copyfile(
            f"{BASE_DIR}/webapp/static/img/placeholder.jpg",
            f"{IMG_PATH}/{img_name}",
        )
        download_log(img_name, img_url)
        log(f"[save_iiif_img] {iiif_url} is not a valid img file", e)
