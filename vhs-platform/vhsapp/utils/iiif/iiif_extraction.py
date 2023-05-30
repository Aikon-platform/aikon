import glob
import os
import time

import requests
from PIL import Image, UnidentifiedImageError

from vhsapp.utils.functions import get_json, create_dir, save_img, sanitize_url
from vhsapp.utils.paths import MEDIA_PATH, IMG_PATH, BASE_DIR
from vhsapp.utils.logger import iiif_log, console, log
from vhsapp.utils.iiif import (
    get_height,
    get_width,
)


def extract_images_from_iiif_manifest(manifest_url, witness_ref):
    """
    Extract all images from an IIIF manifest
    """
    downloader = IIIFDownloader(manifest_url, witness_ref)
    downloader.run()


class IIIFDownloader:
    """Download all image resources from a list of manifest urls."""

    def __init__(
        self,
        manifest_url,
        witness_ref,
        width=None,
        height=None,
        sleep=0.25,
        max_dim=None,
    ):
        self.manifest_url = manifest_url
        self.manifest_id = witness_ref  # Prefix to be used for img filenames
        self.manifest_dir_path = BASE_DIR / IMG_PATH
        self.size = self.get_formatted_size(width, height)
        self.sleep = sleep
        self.max_dim = max_dim  # Maximal height in px

    def run(self):
        manifest = get_json(self.manifest_url)
        if manifest is not None:
            i = 1
            for rsrc in self.get_iiif_resources(manifest):
                is_downloaded = self.save_iiif_img(rsrc, i)
                i += 1
                if is_downloaded:
                    # Gallica is not accepting more than 5 downloads of >1000px / min after
                    time.sleep(12 if "gallica" in self.manifest_url else 0.25)
                    time.sleep(self.sleep)

            # NOTE to create manifests out of images URL
            # with open(BASE_DIR / IMG_PATH / f"{self.manifest_id}.txt", "a") as f:
            #     for img_rsrc in get_iiif_resources(manifest, True):
            #         f.write(
            #             f"{get_height(img_rsrc)} {get_width(img_rsrc)} {get_id(img_rsrc)}\n"
            #         )
            #     f.close()

    def get_formatted_size(self, width="", height=""):
        if not hasattr(self, "max_dim"):
            self.max_dim = None

        if not width and not height:
            if self.max_dim is not None:
                return f",{self.max_dim}"
            return "full"

        if self.max_dim is not None and int(width) > self.max_dim:
            width = f"{self.max_dim}"
        if self.max_dim is not None and int(height) > self.max_dim:
            height = f"{self.max_dim}"

        return f"{width or ''},{height or ''}"

    def save_iiif_img(self, img_rscr, i, size="full", re_download=False):
        img_name = f"{self.manifest_id}_{i:04d}.jpg"

        if (
            glob.glob(os.path.join(self.manifest_dir_path, img_name))
            and not re_download
        ):
            # if the img is already downloaded, don't download it again
            return False

        img_url = self.get_id(img_rscr["service"])
        iiif_url = sanitize_url(f"{img_url}/full/{size}/0/default.jpg")
        console(iiif_url)

        with requests.get(iiif_url, stream=True) as response:
            response.raw.decode_content = True
            try:
                img = Image.open(response.raw)
                img.verify()
            except (UnidentifiedImageError, SyntaxError) as e:
                if size == "full":
                    size = self.get_reduced_size(img_rscr["width"])
                    self.save_iiif_img(img_rscr, i, self.get_formatted_size(size))

                    # TODO mettre sleep here

                    return
                else:
                    log(f"{iiif_url} is not a valid img file: {e}")
                    return
            except (IOError, OSError) as e:
                if size == "full":
                    size = self.get_reduced_size(img_rscr["width"])
                    self.save_iiif_img(img_rscr, i, self.get_formatted_size(size))
                    return
                else:
                    log(f"{iiif_url} is a truncated or corrupted image: {e}")
                    return

            # self.save_img(img, img_name, f"Failed to save {iiif_url}")
            # save_img(img, img_name, f"Failed to save {iiif_url}")

            try:
                img.save(self.manifest_dir_path / img_name)
            except Exception as e:
                log(f"[save_img] Failed to save {iiif_url}:\n{e}")
                return False
        return True

    def get_img_rsrc(self, iiif_img):
        try:
            img_rscr = iiif_img["resource"]
        except KeyError:
            try:
                img_rscr = iiif_img["body"]
            except KeyError:
                return None
        return img_rscr

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
                    f"[get_iiif_resources] Unable to retrieve resources from manifest {manifest}\n{e}"
                )
                return []

        return img_info

    def get_reduced_size(self, size, min_size=1500):
        size = int(size)
        if size < min_size:
            return ""
        if size > min_size * 2:
            return str(int(size / 2))
        return str(min_size)

    def get_id(self, dic):
        if isinstance(dic, list):
            dic = dic[0]

        if isinstance(dic, dict):
            try:
                return dic["@id"]
            except KeyError:
                try:
                    return dic["id"]
                except KeyError as e:
                    log(f"No id provided {e}")

        if isinstance(dic, str):
            return dic

        return None
