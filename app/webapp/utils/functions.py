import datetime
import io
import json
import os
import re
from subprocess import CalledProcessError
import zipfile
from os.path import exists
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import PyPDF2
import requests
from PIL import Image
from django.core.files import File

from django.utils.html import format_html
from django.http import HttpResponse
from django.utils.safestring import mark_safe
from django.core.files import File
from pdf2image import pdfinfo_from_path, convert_from_path
from urllib.request import (
    HTTPPasswordMgrWithDefaultRealm,
    HTTPBasicAuthHandler,
    build_opener,
    install_opener,
)
from app.config.settings import APP_NAME, APP_LANG, CANTALOUPE_APP_URL
from app.webapp.utils.paths import (
    BASE_DIR,
    MEDIA_DIR,
    IMG_PATH,
    PDF_DIR,
)
from app.webapp.models import get_wit_abbr, get_wit_type
from app.webapp.models.utils.constants import MS, VOL, MS_ABBR, VOL_ABBR
from app.webapp.utils.constants import MAX_SIZE, MAX_RES
from app.webapp.utils.logger import log, console


def flatten(l):
    return [item for sublist in l for item in sublist]


def get_last_file(path, prefix):
    pattern = re.compile(r"^{}(\d+)\.\w+$".format(prefix))
    last_number = 0
    for filename in os.listdir(path):
        match = pattern.match(filename)
        if match:
            number = int(match.group(1))
            if number > last_number:
                last_number = number
    return last_number


def to_jpg(image):
    try:
        return save_img(Image.open(image), image.name)
    except Exception as e:
        log("[to_jpg] Failed to convert img to jpg", e)
    return False


def save_img(
    img: Image,
    img_filename,
    img_path=BASE_DIR / IMG_PATH,
    max_dim=MAX_SIZE,
    img_format="JPEG",
):
    try:
        filename = img_filename.split(".")[0]
        if img.mode != "RGB":
            img = img.convert("RGB")

        if img.width > max_dim or img.height > max_dim:
            img.thumbnail(
                (max_dim, max_dim), Image.ANTIALIAS
            )  # Image.Resampling.LANCZOS

        img.save(img_path / f"{filename}.jpg", format=img_format)
        return img
    except Exception as e:
        log("Failed to save img as JPEG", e)
        return False


# def convert_to_jpeg(image):
#     """
#     Convert the image to JPEG format
#     TODO check which performs better
#     """
#     filename = image.name.split(".")[0]
#     img = Image.open(image)
#     if img.mode != "RGB":
#         img = img.convert("RGB")
#     # Create a BytesIO object
#     obj_io = io.BytesIO()
#     # Save image to BytesIO object
#     img.save(obj_io, format="JPEG")
#     # Create a File object
#     img_jpg = File(obj_io, name=f"{filename}.jpg")
#     return img_jpg


def pdf_to_img(event, pdf_name, dpi=MAX_RES):
    """
    Convert the PDF file to JPEG images
    """
    import subprocess

    pdf_path = f"{BASE_DIR}/{MEDIA_DIR}/{pdf_name}"
    pdf_name = Path(pdf_name).stem
    try:
        command = f"pdftoppm -jpeg -r {dpi} -scale-to {MAX_SIZE} {pdf_path} {BASE_DIR / IMG_PATH / pdf_name} -sep _ "
        subprocess.run(command, shell=True, check=True)
        event.set()
    except Exception as e:
        log(
            f"[pdf_to_img] Failed to convert {pdf_name}.pdf to images:\n{e} ({e.__class__.__name__})"
        )


def get_pdf_imgs(pdf_list):
    if type(pdf_list) != list:
        pdf_list = [pdf_list]

    img_list = []
    for pdf_name in pdf_list:
        pdf_reader = PyPDF2.PdfFileReader(
            open(f"{BASE_DIR}/{MEDIA_DIR}/{PDF_DIR}/{pdf_name}", "rb")
        )
        for img_nb in range(1, pdf_reader.numPages + 1):
            img_list.append(
                # name all the pdf images according to the format: "pdf_name_0001.jpg"
                pdf_name.replace(
                    ".pdf", f"_{img_nb:04d}.jpg"
                )  # TODO: here it is retrieving only 4 digits
            )

    return img_list


def credentials(url, auth_user, auth_passwd):
    """
    Basic authentication HTTP request
    """
    passman = HTTPPasswordMgrWithDefaultRealm()
    passman.add_password(None, url, auth_user, auth_passwd)
    handler = HTTPBasicAuthHandler(passman)
    opener = build_opener(handler)
    install_opener(opener)


def gen_link(url, text):
    return format_html(f'<a href="{url}" target="_blank">{text}</a>')


def gen_thumbnail(url, img_url):
    return gen_link(
        url, f"<img src='{img_url}' width='30' style='border-radius:50%;'>)"
    )


def get_icon(icon, color=None):
    if color:
        color = f"style='color: {color}'"
    return mark_safe(f"<i class='fa-solid fa-{icon}' {color}></i>")


def format_start_end(start=None, end=None, no_info="?-?", separator="-"):
    if bool(start) or bool(end):
        start = start or "?"
        end = end or "?"
        if start == end:
            return f"{start}"
        return f"{start}{separator}{end}"
    return no_info


def get_action(action, formatting=None):
    actions = {
        "view": {"en": "visualize", "fr": "visualiser les"},
        "no_manifest": {"en": "no manifest", "fr": "pas de manifest"},
        "no_anno": {"en": "no annotation yet", "fr": "non annoté"},
        "download": {"en": "download", "fr": "télécharger les"},
        "edit": {"en": "edit", "fr": "modifier les"},
        "final": {"en": "final", "fr": "modifier les"},
    }
    action = actions[action][APP_LANG]
    if formatting == "upper":  # => ACTION
        action = action.upper()
    if formatting == "capitalize":  # => Action
        action = action.capitalize()
    return action


def anno_btn(wit_ref, action="view"):
    disabled = ""
    btn = f"{get_action(action, 'upper')} ANNOTATIONS"

    if action == "view":
        color = "#EFB80B"
        tag_id = "annotate_manifest_auto_"
        icon = get_icon("eye")
        btn = f"{action} SOURCE"
    elif action == "edit":
        color = "#008CBA"
        tag_id = "annotate_manifest_"
        icon = get_icon("pen-to-square")
    elif action == "download":
        color = "#ed8a11"
        tag_id = "download_manifest_"
        icon = get_icon("download")
    elif action == "final":
        color = "#4CAF50"
        tag_id = "manifest_final_"
        icon = get_icon("check")
    elif action == "no_manifest" or action == "no_anno":
        btn = get_action(action, "upper")
        color = "#878787"
        tag_id = "annotate_"
        icon = get_icon("eye-slash")
        disabled = "disabled"
    else:
        color = "#B3B3B3"
        tag_id = "annotate_"
        icon = get_icon("eye")

    return (
        f"<button id='{tag_id}{wit_ref}' class='button annotate-manifest' {disabled}"
        f"style='background-color:{color};'>{icon} {btn}</button><br>"
    )


def list_to_txt(item_list, file_name=None):
    if file_name is None:
        file_name = f"{APP_NAME}_export"

    file_name = f"{datetime.date.today()}-{file_name}"

    response = HttpResponse(content_type="text/txt")
    response["Content-Disposition"] = f"attachment; filename={file_name}.txt"

    content = "\n".join(str(item) for item in item_list)
    response.write(content)

    return response


def url_to_name(iiif_img_url):
    return (
        iiif_img_url.replace(f"{CANTALOUPE_APP_URL}/iiif/2/", "")
        .replace("/full/0/default", "")
        .replace("/", "_")
        .replace(".jpg", "")
    )


def zip_img(request, img_list, file_type="img", file_name=f"{APP_NAME}_export"):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        for img_path in img_list:
            img_name = f"{url_to_name(img_path)}.jpg"
            if file_type == "img":
                if urlparse(img_path).scheme == "":
                    z.write(img_path, img_name)
                else:
                    response = requests.get(img_path)
                    if response.status_code == 200:
                        z.writestr(img_name, response.content)
                    else:
                        log(f"[zip_imgs] Fail to download img: {img_path}")
                        pass

    response = HttpResponse(
        buffer.getvalue(), content_type="application/x-zip-compressed"
    )
    response["Content-Disposition"] = f"attachment; filename={file_name}.zip"
    return response


def get_file_list(path, filter_list=None):
    file_list = []
    for folder, _, files in os.walk(path):
        for file in files:
            if filter_list is None or file in filter_list:
                file_list.append(os.path.join(folder, file))
    return file_list


def get_json(url):
    try:
        r = requests.get(url)
    except requests.exceptions.SSLError:
        requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += "HIGH:!DH:!aNULL"
        try:
            requests.packages.urllib3.contrib.pyopenssl.DEFAULT_SSL_CIPHER_LIST += (
                "HIGH:!DH:!aNULL"
            )
        except AttributeError:
            # no pyopenssl support used / needed / available
            pass
        r = requests.get(url, verify=False)

    return json.loads(r.text)


def check_dir(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError("{} does not exist".format(path.absolute()))
    return path


def create_dir(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_files_from_dir(dir_path, valid_extensions=None, recursive=False, sort=False):
    path = check_dir(dir_path)
    if recursive:
        files = [f.absolute() for f in path.glob("**/*") if f.is_file()]
    else:
        files = [f.absolute() for f in path.glob("*") if f.is_file()]

    if valid_extensions is not None:
        valid_extensions = (
            [valid_extensions]
            if isinstance(valid_extensions, str)
            else valid_extensions
        )
        valid_extensions = [
            ".{}".format(ext) if not ext.startswith(".") else ext
            for ext in valid_extensions
        ]
        files = list(filter(lambda f: f.suffix in valid_extensions, files))

    return sorted(files) if sort else files


def check_and_create_if_not(path):
    path = Path(path)
    if not path.exists():
        create_dir(path)
        return False
    return True


def sanitize_url(string):
    return string.replace(" ", "+").replace(" ", "+")


def read_json_file(file_path):
    try:
        with open(file_path) as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        return None


def write_json_file(file_path, dictionary):
    with open(file_path, "w") as file:
        json.dump(dictionary, file)


def get_img_prefix(obj, wit_type=MS):
    img_prefix = f"{get_wit_abbr(wit_type)}{obj.id}"
    if hasattr(obj, f"pdf{wit_type}_set"):
        if getattr(obj, f"pdf{wit_type}_set").first():
            img_prefix = (
                obj.pdfmanuscript_set.first().pdf.name.split("/")[-1].split(".")[0]
            )
    return img_prefix


def get_imgs(img_prefix):
    # TODO make a method of Witness class out of this function
    pattern = re.compile(rf"{img_prefix}_\d{{1,4}}\.jpg", re.IGNORECASE)
    wit_imgs = []

    for img in os.listdir(f"{BASE_DIR}/{IMG_PATH}"):
        if pattern.match(img):
            wit_imgs.append(img)

    return sorted(wit_imgs)


def delete_files(filenames, directory=f"{BASE_DIR}/{IMG_PATH}"):
    if type(filenames) != list:
        filenames = [filenames]

    for file in filenames:
        try:
            os.remove(f"{directory}/{file}")
        except FileNotFoundError:
            log(f"[delete_files] File not found: {directory}/{file}")
        except Exception as e:
            log(f"[delete_files] Error deleting {directory}/{file}: {e}")
    return True
