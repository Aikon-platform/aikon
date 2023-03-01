from uuid import uuid4
from PIL import Image
from io import BytesIO
from pdf2image import pdfinfo_from_path, convert_from_path
from django.core.files import File
from urllib.request import (
    HTTPPasswordMgrWithDefaultRealm,
    HTTPBasicAuthHandler,
    build_opener,
    install_opener,
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
