import datetime
import io
import json
import os
import re
import zipfile
from os.path import exists
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import PyPDF2
import requests
from PIL import Image

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
from vhsapp.models import get_wit_abbr, get_wit_type
from vhsapp.models.constants import MS, VOL, MS_ABBR, VOL_ABBR
from vhsapp.utils.constants import APP_NAME, MAX_SIZE, MAX_RES
from vhsapp.utils.paths import BASE_DIR, MEDIA_PATH, IMG_PATH, MS_PDF_PATH, VOL_PDF_PATH
from vhsapp.utils.logger import log, console


def rename_file(instance, filename, path):
    """
    Rename the file using uuid4
    The file will be uploaded to "{path}/{uuid_filename}"
    """
    extension = filename.split(".")[-1]
    try:
        new_filename = f"{instance.get_wit_ref()}.{extension}"
        if exists(f"{path}/{new_filename}"):
            # TODO: create fct that increment the number if there is already a file named like so
            # here it just erase the currently uploaded file
            new_filename = f"{instance.get_wit_ref()}.{extension}"
    except Exception:
        # Set filename as random string
        new_filename = f"{uuid4().hex}.{extension}"
    # Return the path to the file
    return f"{path}/{new_filename}"


def convert_to_jpeg(image):
    """
    Convert the image to JPEG format
    """
    filename = image.name.split(".")[0]
    img = Image.open(image)
    if img.mode != "RGB":
        img = img.convert("RGB")
    # Create a BytesIO object
    obj_io = io.BytesIO()
    # Save image to BytesIO object
    img.save(obj_io, format="JPEG")
    # Create a File object
    img_jpg = File(obj_io, name=f"{filename}.jpg")
    return img_jpg


def pdf_to_img(pdf_name, dpi=MAX_RES):
    """
    Convert the PDF file to JPEG images
    """
    import subprocess

    pdf_path = f"{BASE_DIR}/{MEDIA_PATH}/{pdf_name}"
    pdf_name = Path(pdf_name).stem
    try:
        command = f"pdftoppm -jpeg -r {dpi} -scale-to {MAX_SIZE} {pdf_path} {BASE_DIR / IMG_PATH / pdf_name} -sep _ "
        subprocess.run(command, shell=True, check=True)
    except Exception as e:
        log(
            f"[pdf_to_img] Failed to convert {pdf_name}.pdf to images:\n{e} ({e.__class__.__name__})"
        )

    # pdf_path = f"{BASE_DIR}/{MEDIA_DIR}/{pdf_name}"
    # Image.MAX_IMAGE_PIXELS = 900000000
    #
    # # e.g. pdf_name = "volumes/pdf/filename.pdf" => "filename"
    # pdf_name = pdf_path.split("/")[-1].split(".")[0] # pdf_path.stem
    # pdf_info = pdfinfo_from_path(pdf_path, userpw=None, poppler_path=None)
    # page_nb = pdf_info["Pages"]
    # step = 2
    # try:
    #     for img_nb in range(1, page_nb + 1, step):
    #         batch_pages = convert_from_path(
    #             pdf_path,
    #             dpi=dpi,
    #             first_page=img_nb,
    #             last_page=min(img_nb + step - 1, page_nb),
    #         )
    #         for page in batch_pages:
    #             save_img(page, f"{pdf_name}_{img_nb:04d}.jpg")
    #             img_nb += 1
    # except Exception as e:
    #     log(f"[pdf_to_img] Failed to convert {pdf_name}.pdf to images:\n{e}")


# def reduce_image_resolution(image, resolution):
#     """
#     Reduce the resolution of the image
#     """
#     width, height = image.size
#     aspect_ratio = width / height
#     new_width = int(resolution * aspect_ratio)
#     reduced_image = image.resize((new_width, resolution), Image.ANTIALIAS)
#     return reduced_image


def save_img(
    img,
    img_filename,
    img_path=BASE_DIR / IMG_PATH,
    error_msg="Failed to save img",
    max_dim=MAX_SIZE,
    img_format="JPEG",
):
    # if glob.glob(img_path / img_filename):
    #     return False  # NOTE: maybe download again anyway because manifest / pdf might have changed

    try:
        if img.width > max_dim or img.height > max_dim:
            img.thumbnail(
                (max_dim, max_dim), Image.ANTIALIAS
            )  # Image.Resampling.LANCZOS
        img.save(img_path / img_filename, format=img_format)
        return True
    except Exception as e:
        log(f"[save_img] {error_msg}:\n{e}")
    return False


def get_pdf_imgs(pdf_list, ps_type=VOL):
    if type(pdf_list) != list:
        pdf_list = [pdf_list]

    path = MS_PDF_PATH if ps_type == MS else VOL_PDF_PATH

    img_list = []
    for pdf_name in pdf_list:
        pdf_reader = PyPDF2.PdfFileReader(
            open(f"{BASE_DIR}/{MEDIA_PATH}/{path}/{pdf_name}", "rb")
        )
        for img_nb in range(1, pdf_reader.numPages + 1):
            img_list.append(
                # name all the pdf images according to the format: "pdf_name_0001.jpg"
                pdf_name.replace(".pdf", f"_{img_nb:04d}.jpg")
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


def anno_btn(wit_ref, action="VISUALIZE"):
    disabled = ""
    btn = f"{action} ANNOTATIONS"

    if action == "VISUALIZE":
        color = "#EFB80B"
        tag_id = "annotate_manifest_auto_"
        icon = get_icon("eye")
        btn = f"{action} SOURCE"
    elif action == "EDIT":
        color = "#008CBA"
        tag_id = "annotate_manifest_"
        icon = get_icon("pen-to-square")
    elif action == "DOWNLOAD":
        color = "#ed8a11"
        tag_id = "download_manifest_"
        icon = get_icon("download")
    elif action == "FINAL":
        color = "#4CAF50"
        tag_id = "manifest_final_"
        icon = get_icon("check")
    elif action == "NO MANIFEST" or action == "NO ANNOTATION YET":
        btn = action
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


def zip_img(img_list, file_type="img", file_name=None):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        for img_path in img_list:
            if file_type == "img":
                if urlparse(img_path).scheme == '':
                    z.write(img_path, os.path.basename(img_path))
                else:
                    response = requests.get(img_path)
                    if response.status_code == 200:
                        z.writestr(os.path.basename(img_path), response.content)
                    else:
                        log(
                            f"[zip_imgs] Fail to download img: {img_path}"
                        )
                        pass
            # elif file_type == "pdf":
            #     if urlparse(img_path).scheme == '':
            #         # Local file path
            #         with open(img_path, "rb") as pdf_file:
            #             pdf_data = pdf_file.read()
            #     else:
            #         pdf_data = requests.get(img_path).content
            #
            #     # Add pdf content to zip
            #     z.writestr(os.path.basename(img_path), pdf_data)

    if file_name is None:
        file_name = f"{APP_NAME}_export_{file_type}"
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


def get_imgs(wit_prefix):
    # TODO make a method of Witness class out of this function
    pattern = re.compile(rf"{wit_prefix}_\d{{4}}\.jpg", re.IGNORECASE)
    wit_imgs = []

    for img in os.listdir(f"{BASE_DIR}/{IMG_PATH}"):
        if pattern.match(img):
            wit_imgs.append(img)

    return wit_imgs
