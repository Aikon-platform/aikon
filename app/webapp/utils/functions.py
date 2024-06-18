import datetime
import fnmatch
import io
import json
import os
import re
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import PyPDF2
import requests
from PIL import Image
from django.core.exceptions import ValidationError

from django.utils.html import format_html
from django.http import HttpResponse
from django.utils.timezone import is_naive, make_aware
from django.utils.safestring import mark_safe
from urllib.request import (
    HTTPPasswordMgrWithDefaultRealm,
    HTTPBasicAuthHandler,
    build_opener,
    install_opener,
)
from app.config.settings import APP_NAME, APP_LANG, CANTALOUPE_APP_URL
from app.webapp.models.utils.constants import DATE_ERROR, IMG
from app.webapp.utils.paths import (
    BASE_DIR,
    MEDIA_DIR,
    IMG_PATH,
    PDF_DIR,
)
from app.webapp.utils.constants import MAX_SIZE, MAX_RES
from app.webapp.utils.logger import log, console


def cls(obj):
    return obj.__class__


def flatten(l):
    return [item for sublist in l for item in sublist]


def flatten_dict(list_of_dicts):
    # list_of_dicts = [ {"key1": "value1", "key2": "value2"}, {"key4": "value4", "key5": "value5"} ]
    # flatten_dict = { "key1": "value1", "key2": "value2", "key4": "value4", "key5": "value5" }
    # same key names results in override
    return dict(**{k: v for d in list_of_dicts for k, v in d.items()})


def extract_nb(string):
    matches = re.compile(r"\d+").findall(string)
    digits = "".join(matches)
    return int(digits) if digits else None


def normalize_str(string):
    string = string.lower().strip().replace("-", "")
    return string


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            if is_naive(obj):
                obj = make_aware(obj)
            return obj.strftime("%Y-%m-%d %H:%M")
        return super().default(obj)


def substrs_in_str(string, substrings):
    for substr in substrings:
        if substr in string:
            return True
    return False


def get_files_with_prefix(path, prefix, filepath="", only_one=False):
    files = []
    with os.scandir(path) as entries:
        for file in entries:
            if file.is_file() and file.name.startswith(prefix):
                if only_one:
                    return file.name
                files.append(f"{filepath}{file.name}")
    return None if only_one else sorted(files)


def get_nb_of_files(path, prefix):
    return len(get_files_with_prefix(path, prefix))


def get_first_img(img_ref):
    for i in range(0, 5):
        if os.path.exists(f"{IMG_PATH}/{img_ref}_{'1'.zfill(i)}.jpg"):
            return f"{img_ref}_{'1'.zfill(i)}.jpg"
    return None


def get_img_nb_len(img_ref):
    img_name = get_first_img(img_ref)
    if img_name:
        return len(img_name.split("_")[-1].split(".")[0])
    return 0


def pluralize(word):
    if APP_LANG == "fr":
        return f"{word}s"

    if re.search("es$", word):
        return word

    if re.search("[sxz]$", word) or re.search("[^aeioudgkprt]h$", word):
        return re.sub("$", "es", word)

    elif re.search("[aeiou]y$", word):
        return re.sub("y$", "ies", word)

    return f"{word}s"


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


def get_file_ext(filepath):
    path, ext = os.path.splitext(filepath)
    _, filename = os.path.split(path)
    return filename if ext else None, ext[1:] if ext else None


def to_jpg(image, new_filename=None):
    try:
        return save_img(Image.open(image), new_filename or image.name)
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
        filename, _ = get_file_ext(img_filename)
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


def rename_file(old_path, new_path):
    if not os.path.exists(old_path):
        log(f"[rename_file] {old_path} does not exist")
        return False
    if os.path.exists(new_path):
        log(f"[rename_file] {new_path} already exists")
    try:
        os.rename(old_path, new_path)
    except Exception as e:
        log(f"[rename_file] {old_path} > {new_path}", e)
        return False
    return True


def temp_to_img(digit, event=None):
    try:
        delete_files(f"{IMG_PATH}/to_delete.txt")

        i = 0
        for i, img_path in enumerate(digit.get_imgs(is_abs=True, temp=True)):
            to_jpg(img_path, digit.get_file_path(i=i + 1))
            print(img_path)
            delete_files(img_path)
        # TODO change to have list of image name
        digit.images.name = f"{i + 1} {IMG} uploaded.jpg"
        if event:
            event.set()
    except Exception as e:
        log(f"[process_images] Failed to process images:\n{e} ({e.__class__.__name__})")


def pdf_to_img(pdf_name, event=None, dpi=MAX_RES):
    """
    Convert the PDF file to JPEG images
    """
    import subprocess

    pdf_path = f"{MEDIA_DIR}/{pdf_name}"
    pdf_name = Path(pdf_name).stem
    try:
        command = f"pdftoppm -jpeg -r {dpi} -scale-to {MAX_SIZE} {pdf_path} {IMG_PATH}/{pdf_name} -sep _ "
        subprocess.run(command, shell=True, check=True)
        if event:
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
            open(f"{MEDIA_DIR}/{PDF_DIR}/{pdf_name}", "rb")
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


def mono_val(val):
    if type(val) in [str, int]:
        return val
    if type(val) == dict:
        if len(val.keys()) == 1:
            val = list(val.values())[0]
    if type(val) == list and len(val) == 1:
        val = val[0]
    return val


def extract_urls(input_string):
    url_pattern = re.compile(r"https?://\S+")
    unique_urls = set(re.findall(url_pattern, input_string))
    return mono_val(list(unique_urls))


def gen_link(url, text):
    return format_html(f'<a href="{url}" target="_blank">{text}</a>')


def gen_thumbnail(url, img_url):
    return gen_link(
        url, f"<img src='{img_url}' width='30' style='border-radius:10%;'>)"
    )


def format_dates(min_date=None, max_date=None):
    if min_date == max_date:
        return min_date or "-"
    else:
        if min_date is None or max_date is None:
            year = max_date if min_date is None else min_date
            return f"c. {year}"
        return f"{min_date}-{max_date}"


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
        "view": {"en": "visualize source", "fr": "visualiser la source"},
        "auto-view": {
            "en": "visualize automatic regions",
            "fr": "voir les régions automatiques",
        },
        "similarity": {"en": "compare regions", "fr": "comparer les régions"},
        "no_manifest": {"en": "no manifest", "fr": "pas de manifest"},
        "no_digit": {"en": "no digitization", "fr": "pas de numérisation"},
        "no_img": {"en": "no image", "fr": "pas d'image"},
        "no_regions": {"en": "no regions yet", "fr": "pas de régions"},
        "download": {"en": "download regions", "fr": "télécharger les régions"},
        "edit": {"en": "edit regions", "fr": "modifier les régions"},
        "final": {"en": "visualize final regions", "fr": "voir les régions finales"},
        "crops": {
            "en": "all regions",
            "fr": "toutes les régions",
        },
        "vectors": {
            "en": "visualize automatic vectorizations",
            "fr": "voir les vectorisations automatiques",
        },
    }
    action = actions[action][APP_LANG]
    if formatting == "upper":  # => ACTION
        action = action.upper()
    if formatting == "capitalize":  # => Action
        action = action.capitalize()
    return action


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


def zip_img(img_list, zip_name=f"{APP_NAME}_export"):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        for img_path in img_list:
            img_name = f"{url_to_name(img_path)}.jpg"
            if urlparse(img_path).scheme == "":
                z.write(f"{IMG_PATH}/{img_name}", img_name)
            else:
                response = requests.get(img_path)
                if response.status_code == 200:
                    z.writestr(img_name, response.content)
                else:
                    log(f"[zip_img] Fail to download img: {img_path}")
                    pass

    response = HttpResponse(
        buffer.getvalue(), content_type="application/x-zip-compressed"
    )
    response["Content-Disposition"] = f"attachment; filename={zip_name}.zip"
    return response


def zip_files(filenames_contents, zip_name=f"{APP_NAME}_export"):
    # filenames_contents = [(filename1, content1), (filename2, content2), ...]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        for filename_content in filenames_contents:
            filename, content = filename_content
            z.writestr(filename, content)

    response = HttpResponse(
        buffer.getvalue(), content_type="application/x-zip-compressed"
    )
    response["Content-Disposition"] = f"attachment; filename={zip_name}.zip"
    return response


def zip_dirs(dirnames_contents, zip_name=f"{APP_NAME}_export"):
    # dirnames_contents = {
    #   dir1: [(filename1, content1), (filename2, content2), ...],
    #   dir2: [(filename1, content1), (filename2, content2), ...]
    #   dir3: ...
    # }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        for dirname, filename_contents in dirnames_contents.items():
            z.writestr(f"{dirname}/", "")

            for filename_content in filename_contents:
                filename, content = filename_content
                if type(content) == str:
                    z.writestr(f"{dirname}/{filename}", content)

    response = HttpResponse(
        buffer.getvalue(), content_type="application/x-zip-compressed"
    )
    response["Content-Disposition"] = f"attachment; filename={zip_name}.zip"
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


def delete_files(filenames, directory=IMG_PATH):
    if type(filenames) != list:
        filenames = [filenames]

    for file in filenames:
        file_path = os.path.join(directory, file)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                log(f"[delete_files] Error deleting {file_path}", e)
        else:
            print(f"[delete_files] File not found: {file_path}")
    return True


def validate_dates(date_min, date_max):
    # TODO: needs improvement
    if date_min and date_max and date_min > date_max:
        raise ValidationError(DATE_ERROR)


def truncate_words(text, max_length):
    words = text.split()
    if len(words) > 2 * max_length:  # Check if the text is longer than 2*TRUNCATEWORDS
        return " ".join(words[:max_length] + ["..."] + words[-max_length:])
    return text


def sort_key(s):
    return [int(part) if part.isdigit() else part for part in re.split("(\d+)", s)]
