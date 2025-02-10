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
    downloader = IIIFDownloader(manifest_url, digit_ref)
    downloader.run()

    if lic := downloader.original_license:
        license_url = get_license_url(lic)
        attribution = downloader.attribution or "Unknown attribution"
        digit.add_info(license_url, attribution)


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

    except (RequestException, ProtocolError, Timeout, Exception) as e:
        shutil.copyfile(
            f"{BASE_DIR}/webapp/static/img/placeholder.jpg",
            f"{IMG_PATH}/{img_name}",
        )
        download_log(img_name, img_url)
        log(f"[save_iiif_img] {iiif_url} is not a valid img file", e)


class IIIFDownloader:
    """Download all image resources from a list of manifest urls."""

    def __init__(
        self,
        manifest_url,
        witness_ref,
        sleep=0.25,
        max_dim=MAX_SIZE,
        min_dim=1500,
    ):
        self.manifest_url = manifest_url
        self.manifest_id = witness_ref  # Prefix to be used for img filenames
        self.manifest_dir_path = BASE_DIR / IMG_PATH

        # self.size = self.get_formatted_size(width, height)
        self.max_dim = max_dim  # Maximal height in px
        self.min_dim = (
            1000 if "gallica" in self.manifest_url else min_dim
        )  # Minimal height in px

        # Gallica is not accepting more than 5 downloads of >1000px / min after
        self.sleep = 12 if "gallica" in self.manifest_url else sleep
        # Save the license given in the original manifest if possible
        self.original_license = ""
        self.attribution = ""

    def run(self):
        manifest = get_json(self.manifest_url)
        if manifest is not None:
            i = 1
            self.get_license(manifest)
            self.get_attribution(manifest)

            for rsrc in self.get_iiif_resources(manifest):
                self.save_iiif_img(rsrc, i)
                i += 1

            if DOWNLOAD_LOG_PATH:
                with open(DOWNLOAD_LOG_PATH, "r") as f:
                    images = f.read().splitlines()
                images = list(filter(None, images))
                open(DOWNLOAD_LOG_PATH, "w").close()

                for image in images:
                    save_failed_img(image)

            # NOTE to create manifests out of images URL
            # with open(BASE_DIR / IMG_PATH / f"{self.manifest_id}.txt", "a") as f:
            #     for img_rsrc in get_iiif_resources(manifest, True):
            #         f.write(
            #             f"{get_height(img_rsrc)} {get_width(img_rsrc)} {get_id(img_rsrc)}\n"
            #         )
            #     f.close()

    def get_license(self, manifest):
        from app.webapp.utils.iiif.manifest import get_meta_value

        if "license" in manifest:
            self.original_license = manifest["license"]
            return

        labels = [
            "license",
            "license",
            "lizenz",
            "rights",
            "droits",
            "access",
            "copyright",
            "rechteinformationen",
            "conditions",
        ]
        if "metadata" not in manifest:
            return
        for label in labels:
            for metadatum in manifest["metadata"]:
                if value := get_meta_value(metadatum, label):
                    self.original_license = value
                    return

        if "attribution" in manifest:
            self.original_license = manifest["attribution"]
        return

    def get_attribution(self, manifest):
        if "attribution" in manifest:
            self.attribution = manifest["attribution"]
        return

    def save_iiif_img(self, img_rsrc, i, size=None, re_download=False):
        img_name = f"{self.manifest_id}_{i:04d}.jpg"
        f_size = size or self.get_size(img_rsrc)

        # NOTE: maybe download again anyway because manifest might have changed
        if (
            glob.glob(os.path.join(self.manifest_dir_path, img_name))
            and not re_download
        ):
            img = Image.open(self.manifest_dir_path / img_name)
            if self.check_size(img, img_rsrc):
                # if the img is already downloaded and has the correct size, don't download it again
                return False

        img_url = get_id(img_rsrc["service"])
        iiif_url = sanitize_url(f"{img_url}/full/{f_size}/0/default.jpg")

        time.sleep(self.sleep)

        try:
            with requests.get(iiif_url, stream=True) as response:
                response.raw.decode_content = True
                try:
                    img = Image.open(response.raw)
                except (UnidentifiedImageError, SyntaxError) as e:
                    time.sleep(self.sleep)
                    if size == f_size:
                        size = self.get_reduced_size(img_rsrc)
                        self.save_iiif_img(img_rsrc, i, self.get_formatted_size(size))
                        return
                    else:
                        shutil.copyfile(
                            f"{BASE_DIR}/webapp/static/img/placeholder.jpg",
                            f"{IMG_PATH}/{img_name}",
                        )
                        download_log(img_name, img_url)
                        log(f"[save_iiif_img] {iiif_url} is not a valid img file", e)
                        return
                except (IOError, OSError) as e:
                    if size == "full":
                        size = self.get_reduced_size(img_rsrc)
                        self.save_iiif_img(img_rsrc, i, self.get_formatted_size(size))
                        return
                    else:
                        log(
                            f"[save_iiif_img] {iiif_url} is a truncated or corrupted image",
                            e,
                        )
                        return
                return save_img(img, img_name)

        except (RequestException, ProtocolError, Timeout, ConnectionError) as e:
            download_log(img_name, img_url)
            log(f"[save_iiif_img] Failed to download image from {iiif_url}", e)
            return False

    def get_img_rsrc(self, iiif_img):
        try:
            img_rsrc = iiif_img["resource"]
        except KeyError:
            try:
                img_rsrc = iiif_img["body"]
            except KeyError:
                return None
        return img_rsrc

    def get_iiif_resources(self, manifest, only_img_url=False):
        try:
            # Usually images URL are contained in the "canvases" field
            img_list = [
                canvas["images"] for canvas in manifest["sequences"][0]["canvases"]
            ]
            img_info = [self.get_img_rsrc(img) for imgs in img_list for img in imgs]
        except KeyError:
            # But sometimes in the "items" field
            try:
                img_list = [
                    item
                    for items in manifest["items"]
                    for item in items["items"][0]["items"]
                ]
                img_info = [self.get_img_rsrc(img) for img in img_list]
            except KeyError as e:
                log(
                    f"[get_iiif_resources] Unable to retrieve resources from manifest {self.manifest_url}",
                    e,
                )
                return []

        return img_info

    def get_size(self, img_rsrc):
        if self.max_dim is None:
            return "full"
        h, w = get_height(img_rsrc), get_width(img_rsrc)
        if h is None or w is None:
            return self.get_formatted_size(str(self.max_dim), "")
        if h > w:
            max_h = self.max_dim if self.max_dim < h else h
            return self.get_formatted_size("", str(max_h))
        max_w = self.max_dim if self.max_dim < w else w
        return self.get_formatted_size(str(max_w), "")

    def check_size(self, img, img_rsrc):
        """
        Checks if an already downloaded image has the correct dimensions
        """
        if self.max_dim is None:
            if int(img.height) == get_height(img_rsrc):  # for full size
                return True

        if int(img.height) == self.max_dim or int(img.width) == self.max_dim:
            # if either the height or the width corresponds to max dimension
            # if it is too big, re-download again
            return True

        return False  # Download again

    def get_formatted_size(self, width="", height=""):
        if not hasattr(self, "max_dim"):
            self.max_dim = None

        if not width and not height:
            if self.max_dim is not None:
                return f",{self.max_dim}"
            return "full"

        if width and self.max_dim and int(width) > self.max_dim:
            width = f"{self.max_dim}"
        if height and self.max_dim and int(height) > self.max_dim:
            height = f"{self.max_dim}"

        return f"{width or ''},{height or ''}"

    def get_reduced_size(self, img_rsrc):
        h, w = get_height(img_rsrc), get_width(img_rsrc)
        larger_side = h if h > w else w

        if larger_side < self.min_dim:
            return ""
        if larger_side > self.min_dim * 2:
            return str(int(larger_side / 2))
        return str(self.min_dim)
