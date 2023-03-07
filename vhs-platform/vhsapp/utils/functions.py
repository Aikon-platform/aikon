import csv
import io
import os
from uuid import uuid4

import PyPDF2
import requests
from PIL import Image
from io import BytesIO

from django.utils.html import format_html
from django.http import HttpResponse
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


def rename_file(instance, filename, path):
    """
    Rename the file using uuid4
    The file will be uploaded to "{path}/{uuid_filename}"
    """
    extension = filename.split(".")[-1]
    # Set filename as random string
    uuid_filename = "{}.{}".format(uuid4().hex, extension)
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
    img_jpg = File(obj_io, name="{}.jpg".format(filename))
    return img_jpg


def convert_pdf_to_image(pdf_path, image_path):
    """
    Convert the PDF file to JPEG images
    """
    pdf_file = pdf_path.split("/")[-1]
    filename = pdf_file.split(".")[0]
    pdf_info = pdfinfo_from_path(pdf_path, userpw=None, poppler_path=None)
    number_pages = pdf_info["Pages"]
    step = 2
    for image_counter in range(1, number_pages + 1, step):
        batch_pages = convert_from_path(
            pdf_path,
            dpi=300,
            first_page=image_counter,
            last_page=min(image_counter + step - 1, number_pages),
        )
        # Iterate through all the batch pages stored above
        for page in batch_pages:
            pathname = f"{image_path}{filename}_{image_counter:04d}.jpg"
            # Save the image of the page in IMAGES_PATH
            page.save(pathname, format="JPEG")
            # Increment the counter to update filename
            image_counter += 1


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


def log(msg="🚨🚨🚨"):
    import logging

    logger = logging.getLogger("django")
    logger.info(msg)


def get_icon(icon):
    return f"<i class='fa-solid fa-{icon}'></i>"


def anno_btn(obj_id, action="VISUALIZE"):
    match action:
        case "VISUALIZE":
            color = "#EFB80B"
            tag_id = "annotate_manifest_auto_"
            icon = get_icon("eye")
        case "EDIT":
            color = "#008CBA"
            tag_id = "annotate_manifest_"
            icon = get_icon("pen-to-square")
        case "DOWNLOAD":
            color = "#ed8a11"
            tag_id = "download_manifest_"
            icon = get_icon("download")
        case "FINAL":
            color = "#4CAF50"
            tag_id = "manifest_final_"
            icon = get_icon("check-square-o")
        case _:
            color = "#B3B3B3"
            tag_id = "annotate_"
            icon = get_icon("eye")

    return (
        f"<button id='{tag_id}{obj_id}' class='button annotate-manifest' "
        f"style='background-color:{color};'>{icon} {action} ANNOTATIONS</button><br>"
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
            match file_type:
                case "img":
                    # Add file to zip
                    z.write(img_path, os.path.basename(img_path))
                case "pdf":
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


def pdf_to_imgs(pdf_list, ps_type="volume"):
    if type(pdf_list) != list:
        pdf_list = [pdf_list]

    img_list = []
    for pdf in pdf_list:
        pdf_file = open(f"mediafiles/{ps_type}/pdf/" + pdf, "rb")
        pdf_reader = PyPDF2.PdfFileReader(pdf_file)
        for img_nb in range(1, pdf_reader.numPages + 1):
            img_list.append(
                # name all the pdf images according to the format: "pdf_name_0001.jpg"
                pdf.replace(".pdf", "_{:04d}".format(img_nb) + ".jpg")
            )

        # pdf_file = Pdf.open("mediafiles/volumes/pdf/" + pdf)
        # for img_nb in range(1, len(pdf_file.pages) + 1):
        #     img_list.append(pdf.replace(".pdf", "_{:04d}".format(img_nb) + ".jpg"))

    return img_list
