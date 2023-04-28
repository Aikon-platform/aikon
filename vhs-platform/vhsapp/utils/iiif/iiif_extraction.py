import os

import requests
from PIL import Image, UnidentifiedImageError

from vhsapp.utils.functions import get_json, create_dir, save_img
from vhsapp.utils.paths import MEDIA_PATH, IMG_PATH, BASE_DIR
from vhsapp.utils.logger import iiif_log, console, log
from vhsapp.utils.iiif.iiif_utils import (
    get_id,
    get_height,
    get_width,
    get_formatted_size,
    get_iiif_resources,
)


def extract_images_from_iiif_manifest(manifest_url, work):
    """
    Extract all images from an IIIF manifest
    """
    manifest = get_json(manifest_url)
    if manifest is not None:
        file_name = f"{work}.txt"
        if not os.path.isfile(BASE_DIR / IMG_PATH):
            create_dir(BASE_DIR / IMG_PATH)
        with open(BASE_DIR / IMG_PATH / file_name, "a") as f:
            for img_rsrc in get_iiif_resources(manifest, True):
                f.write(
                    f"{get_height(img_rsrc)} {get_width(img_rsrc)} {get_id(img_rsrc)}\n"
                )
            f.close()
        # else:
        #     manifest_id = Path(urlparse(get_id(manifest)).path).parent.name
        #     i = 1
        #     for img_rscr in get_iiif_resources(manifest, True):
        #         is_downloaded = save_iiif_img(img_rscr, i, work)
        #         i += 1
        #         if is_downloaded:
        #             time.sleep(5 if "gallica" in manifest_url else 0.25)


# NOT USED
def get_reduced_size(size, min_size=1500):
    size = int(size)
    if size < min_size:
        return ""
    if size > min_size * 2:
        return str(int(size / 2))
    return str(min_size)


# NOT USED
def save_iiif_img(img_rscr, i, work, size="full", re_download=False):
    img_name = f"{work}_{i:04d}.jpg"

    if os.path.isfile(BASE_DIR / IMG_PATH / img_name) and not re_download:
        # if the img is already downloaded, don't download it again
        return False

    img_url = get_id(img_rscr["service"])
    iiif_url = f"{img_url}/full/{size}/0/default.jpg"

    with requests.get(iiif_url, stream=True) as response:
        response.raw.decode_content = True
        try:
            img = Image.open(response.raw)
        except UnidentifiedImageError:
            if size == "full":
                size = get_reduced_size(img_rscr["width"])
                save_iiif_img(img_rscr, i, work, get_formatted_size(size))
                return
            else:
                log(f"[save_iiif_img] Failed to extract images from {img_url}")
                iiif_log(img_url)
                return

        save_img(img, img_name, f"Failed to extract from {img_url}")
    return True
