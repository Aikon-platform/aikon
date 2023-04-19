import csv
import io
import json
import os
import shutil
from pathlib import Path
from uuid import uuid4

import PyPDF2
import requests
from PIL import Image
from io import BytesIO

from django.utils.html import format_html
from django.http import HttpResponse
from django.utils.safestring import mark_safe
from pdf2image import pdfinfo_from_path, convert_from_path
from django.core.files import File
from urllib.request import (
    HTTPPasswordMgrWithDefaultRealm,
    HTTPBasicAuthHandler,
    build_opener,
    install_opener,
)
from vhsapp.utils.constants import (
    APP_NAME,
)
from vhsapp.utils.paths import BASE_DIR, MEDIA_PATH, IMG_PATH
from vhsapp.utils.logger import log, console


def rename_file(instance, filename, path):
    """
    Rename the file using uuid4
    The file will be uploaded to "{path}/{uuid_filename}"
    """
    extension = filename.split(".")[-1]
    # Set filename as random string
    uuid_filename = f"{uuid4().hex}.{extension}"
    # Return the path to the file
    return f"{path}/{uuid_filename}"


def convert_to_jpeg(image):
    """
    Convert the image to JPEG format
    """
    filename = image.name.split(".")[0]
    img = Image.open(image)
    if img.mode != "RGB":
        img = img.convert("RGB")
    # Create a BytesIO object
    obj_io = BytesIO()
    # Save image to BytesIO object
    img.save(obj_io, format="JPEG")
    # Create a File object
    img_jpg = File(obj_io, name=f"{filename}.jpg")
    return img_jpg


def convert_pdf_to_image(pdf_name):
    """
    TODO: remove because turned into method of the PDF class
    Convert the PDF file to JPEG images
    """
    pdf_path = f"{BASE_DIR}/{MEDIA_PATH}/{pdf_name}"
    # e.g. pdf_name = "volumes/pdf/filename.pdf" => filename = "filename"
    filename = pdf_path.split("/")[-1].split(".")[0]
    pdf_info = pdfinfo_from_path(pdf_path, userpw=None, poppler_path=None)
    page_nb = pdf_info["Pages"]
    step = 2
    try:
        for img_nb in range(1, page_nb + 1, step):
            batch_pages = convert_from_path(
                pdf_path,
                dpi=300,
                first_page=img_nb,
                last_page=min(img_nb + step - 1, page_nb),
            )
            # Iterate through all the batch pages stored above
            for page in batch_pages:
                page.save(
                    f"{BASE_DIR}/{IMG_PATH}/{filename}_{img_nb:04d}.jpg", format="JPEG"
                )
                # Increment the counter to update filename
                img_nb += 1
    except Exception as e:
        log(f"Failed to convert {filename}.pdf to images:\n{e}")


def get_pdf_imgs(pdf_list, ps_type="volume"):
    if type(pdf_list) != list:
        pdf_list = [pdf_list]

    img_list = []
    for pdf_name in pdf_list:
        pdf_reader = PyPDF2.PdfFileReader(
            open(f"{MEDIA_PATH}/{ps_type}/pdf/{pdf_name}", "rb")
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


def anno_btn(obj_id, action="VISUALIZE"):
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
        icon = get_icon("check-square-o")
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
        f"<button id='{tag_id}{obj_id}' class='button annotate-manifest' {disabled}"
        f"style='background-color:{color};'>{icon} {btn}</button><br>"
    )


def list_to_csv(item_list, first_row=None, file_name=None):
    if file_name is None:
        file_name = f"{APP_NAME}_export"

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f"attachment; filename={file_name}.csv"

    writer = csv.writer(response)
    if first_row:
        writer.writerow([first_row])

    writer.writerow([item] for item in item_list)
    return response


def zip_img(zip_file, img_list, file_type="img", file_name=None):  # maybe change name
    buffer = io.BytesIO()
    with zip_file.ZipFile(buffer, "w") as z:
        for img_path in img_list:
            if file_type == "img":
                # Add file to zip
                z.write(img_path, os.path.basename(img_path))
            elif file_type == "pdf":
                pdf_data = requests.get(img_path).content
                # Add pdf content to zip
                z.writestr(os.path.basename(img_path), pdf_data)

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


def save_img(img: Image, img_filename, error_msg="Failed to save img"):
    try:
        img.save(BASE_DIR / IMG_PATH / img_filename)
        # with open(BASE_DIR / IMG_PATH / img_filename, mode="wb") as f:
        #     shutil.copyfileobj(img, f)
        #     # f.write(image_response.content)
    except Exception as e:
        log(f"{error_msg}:\n{e}")
