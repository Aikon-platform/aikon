import re
import json
import requests
import time
from uuid import uuid4
from PIL import Image
from io import BytesIO
from tripoli import IIIFValidator
from pdf2image import pdfinfo_from_path, convert_from_path
from django.core.files import File
from django.core.exceptions import ValidationError
from urllib.request import (
    HTTPPasswordMgrWithDefaultRealm,
    HTTPBasicAuthHandler,
    build_opener,
    install_opener,
)


# Validate the pattern of a Gallica manifest URL
def validate_gallica_manifest_url(value):
    # Check if the hostname of the URL matches the desired pattern
    hostname = re.match(r"https?://(.*?)/", value).group(1)
    if hostname == "gallica.bnf.fr":
        # Define the regular expression pattern for a valid Gallica manifest URL
        pattern = re.compile(
            r"https://gallica.bnf.fr/iiif/ark:/12148/[a-z0-9]+/manifest.json"
        )
        match = bool(pattern.match(value))
        # Check if the URL matches the pattern
        if not match:
            raise ValidationError("URL de manifeste Gallica non valide.")


"""
Validate a IIIF manifest using Tripoli
Check if the manifest conforms to the IIIF Presentation API 2.1 specification
"""


def validate_iiif_manifest(url):
    try:
        response = requests.get(url)
        manifest = json.loads(response.text)
        validator = IIIFValidator()
        validator.validate(manifest)
    except Exception:
        raise ValidationError("Manifeste IIIF non valide.")


"""
Rename the file using uuid4
The file will be uploaded to "{path}/{uuid_filename}"
"""


def rename_file(instance, filename, path):
    extension = filename.split(".")[-1]
    # Set filename as random string
    uuid_filename = "{}.{}".format(uuid4().hex, extension)
    # Return the path to the file
    return f"{path}/{uuid_filename}"


# Convert the image to JPEG format
def convert_to_jpeg(image):
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


# Convert the PDF file to JPEG images
def convert_pdf_to_image(pdf_path, image_path):
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


# Extract all images from an IIIF manifest
def extract_images_from_iiif_manifest(url, image_path, work):
    response = requests.get(url)
    manifest = json.loads(response.text)
    image_counter = 1
    for sequence in manifest["sequences"]:
        for canvas in sequence["canvases"]:
            for image in canvas["images"]:
                image_url = (
                    f"{image['resource']['service']['@id']}/full/full/0/default.jpg"
                )
                image_response = requests.get(image_url)
                with open(f"{image_path}{work}_{image_counter:04d}.jpg", "wb") as f:
                    f.write(image_response.content)
                image_counter += 1
                time.sleep(15)


# Basic authentication HTTP request
def credentials(url, auth_user, auth_passwd):
    passman = HTTPPasswordMgrWithDefaultRealm()
    passman.add_password(None, url, auth_user, auth_passwd)
    handler = HTTPBasicAuthHandler(passman)
    opener = build_opener(handler)
    install_opener(opener)
