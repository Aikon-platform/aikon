import datetime
import shutil

import magic
import io
import json
import os
import re
import zipfile
import imagesize
from pathlib import Path
from typing import Optional, List
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
    IMG_PATH,
)
from app.vectorization.const import SVG_PATH
from app.webapp.utils.constants import MAX_SIZE
from app.webapp.utils.logger import log


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


def get_files_in_dir(path, include_subdir=False):
    """
    Returns a list of filenames in the specified directory.

    Args:
        path (str): Path to the directory.
        include_subdir (bool): Whether to include files in subdirectories.

    Returns:
        list: List of filenames (with relative paths if subdirectories are included).
    """
    if not os.path.isdir(path):
        raise ValueError(f"{path} is not a valid directory.")

    if include_subdir:
        return [
            os.path.relpath(os.path.join(root, file), path)
            for root, _, files in os.walk(path)
            for file in files
        ]
    return [
        file for file in os.listdir(path) if os.path.isfile(os.path.join(path, file))
    ]


def get_files_with_prefix(
    path: str,
    prefix: str,
    filepath: str = "",
    only_one: bool = False,
    ext: Optional[str] = None,
):
    """
    Efficiently retrieve files with a given prefix in a directory.

    :param path: Directory path to search in
    :param prefix: Prefix to match at the beginning of file names
    :param filepath: Additional path to prepend to filenames (default: "")
    :param only_one: If True, return the first matching file (default: False)
    :param ext: File extension to filter by (default: None)
    :return: A single filename (if only_one is True), a list of filenames, or None if no matches found
    """
    if not os.path.exists(path):
        return [] if not only_one else None

    with os.scandir(path) as entries:
        if only_one:
            for entry in entries:
                if entry.is_file() and entry.name.startswith(prefix):
                    if ext and not entry.name.endswith(ext):
                        continue
                    return f"{filepath}{entry.name}"
            return None

        return [
            f"{filepath}{e.name}"
            for e in entries
            if e.is_file()
            and e.name.startswith(prefix)
            and (not ext or e.name.endswith(ext))
        ]


def get_nb_of_files(path, prefix):
    return len(get_files_with_prefix(path, prefix)) or 0


def get_first_img(img_ref):
    for i in range(0, 5):
        img_name = f"{img_ref}_{'1'.zfill(i)}.jpg"
        if os.path.exists(f"{IMG_PATH}/{img_name}"):
            return img_name
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


Image.MAX_IMAGE_PIXELS = 200000000


def check_image(file_path, max_size=10, max_pixels=Image.MAX_IMAGE_PIXELS):
    if not os.path.exists(file_path):
        return False, "File does not exist"

    file_size = os.path.getsize(file_path) / (1024 * 1024)
    if file_size > max_size:
        return False, f"File too large: {file_size:.2f}MB (max: {max_size}MB)"

    try:
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(file_path)
        if not file_type.startswith("image/"):
            return False, f"Not an image file: {file_type}"
    except Exception as e:
        return False, f"Error determining file type: {e}"

    try:
        width, height = imagesize.get(file_path)
        pixels = width * height
        if pixels > max_pixels:
            return False, f"Image too large: {width}x{height} ({pixels} pixels)"
        return True, {
            "width": width,
            "height": height,
            "format": file_type,
            "size_mb": file_size,
        }
    except Exception as e:
        return False, f"Error determining image dimensions: {e}"


def to_jpg(image, new_filename=None):
    is_valid, info = check_image(image)
    if not is_valid:
        log(f"[to_jpg] {info}")
        return False

    try:
        return save_img(Image.open(image), new_filename or image.name)
    except Exception as e:
        log("[to_jpg] Failed to convert img to jpg", e)
    return False


def save_img(
    img: Image,
    img_filename,
    img_path=IMG_PATH,
    max_dim=MAX_SIZE,
    img_format="JPEG",
):
    try:
        filename, _ = get_file_ext(img_filename)
        if img.mode != "RGB":
            img = img.convert("RGB")

        if img.width > max_dim or img.height > max_dim:
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

        img.save(img_path / f"{filename}.jpg", format=img_format)
        return f"{filename}.jpg"
    except Exception as e:
        log("Failed to save img as JPEG", e)
        return False


def rename_file(old_path, new_path):
    if not os.path.exists(old_path):
        log(f"[rename_file] {old_path} does not exist")
        return False
    if os.path.exists(new_path):
        log(f"[rename_file] {new_path} already exists, overriding its content")
    try:
        os.rename(old_path, new_path)
    except Exception as e:
        log(f"[rename_file] {old_path} > {new_path}", e)
        return False
    return True


def temp_to_img(digit):
    img_filenames = []
    try:
        delete_files(f"{IMG_PATH}/to_delete.txt")

        i = 0
        for i, img_path in enumerate(
            digit.get_imgs(is_abs=True, temp=True, check_in_dir=True)
        ):
            img_filename = to_jpg(img_path, digit.get_file_path(i=i + 1))
            if img_filename:
                img_filenames.append(img_filename)
            delete_files(img_path)
        # TODO change to have list of image names
        digit.images.name = f"{i + 1} {IMG} uploaded.jpg"

    except Exception as e:
        log(f"[process_images] Failed to process images", exception=e)
        return False
    return img_filenames


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
        "regions": {
            "en": "all regions",
            "fr": "toutes les régions",
        },
        "vectors": {
            "en": "visualize automatic vectorizations",
            "fr": "voir les vectorisations automatiques",
        },
        "vectorization": {
            "en": "perform vectorization",
            "fr": "vectorisation automatique",
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


def zip_images_and_files(img_list, file_list, zip_name=f"{APP_NAME}_export"):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        # Ajouter des images à partir des URLs ou du répertoire local
        for img_path in img_list:
            img_name = f"{url_to_name(img_path)}.jpg"
            if urlparse(img_path).scheme == "":
                try:
                    z.write(f"{SVG_PATH}/{img_name}", img_name)
                except FileNotFoundError:
                    log(f"[zip_images_and_files] Local image not found: {img_path}")
            else:
                response = requests.get(img_path)
                if response.status_code == 200:
                    z.writestr(img_name, response.content)
                else:
                    log(f"[zip_images_and_files] Fail to download image: {img_path}")

        # Ajouter des fichiers à partir du répertoire mediafiles
        for file_path in file_list:
            try:
                with open(f"{SVG_PATH}/{file_path}", "rb") as f:
                    z.writestr(file_path, f.read())
            except FileNotFoundError:
                log(f"[zip_images_and_files] Local file not found: {file_path}")

    response = HttpResponse(
        buffer.getvalue(), content_type="application/x-zip-compressed"
    )
    response["Content-Disposition"] = f"attachment; filename={zip_name}.zip"
    return response


def is_url(chaine):
    """
    Vérifie si une chaîne est une URL.

    Args:
      chaine: string à tester.

    Returns:
      True si la chaîne est une URL, False sinon.
    """

    regex = r"^(http|https)://.*"
    return re.search(regex, chaine) is not None


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
        file_path = file if os.path.isabs(file) else os.path.join(directory, file)
        if os.path.exists(file_path):
            delete_path(file_path)
        else:
            log(f"[delete_files] File not found: {file_path}")
    return True


def delete_path(path: Path) -> bool:
    """
    Delete a file or directory

    Returns True if the path existed and was deleted, False otherwise
    """
    try:
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
    except Exception:
        try:
            os.chmod(path, 0o777)  # Change permissions to allow deletion
            os.remove(path)
        except Exception as e:
            log(f"[delete_path] Error deleting {path}", e)
            return False
    return True


def validate_dates(date_min, date_max):
    # TODO: needs improvement
    if date_min and date_max and date_min > date_max:
        raise ValidationError(DATE_ERROR)


def truncate_words(text, max_words):
    words = text.split()
    if len(words) > 2 * max_words:  # Check if the text is longer than 2*TRUNCATEWORDS
        return " ".join(words[:max_words] + ["…"] + words[-max_words:])
    return text


def truncate_char(text, max_length):
    if len(text) > max_length:  # Check if the text is longer than 2*TRUNCATECHAR
        return text[: max_length - 1] + "…"
    return text


def sort_key(s: str) -> List[str | int]:
    """
    sorting key for witness and regions ids: used in `sorted()` functions to sort list of region ids or image ids alphabetically

    :example:
    >>> sort_key("wit1_pdf3_anno2")
    ... ['wit', 1, '_pdf', 3, '_anno', 2, '']

    >>> sort_key("wit3_pdf8_01_122,286,220,1128")
    ... ['wit', 3, '_pdf', 8, '_', 1, '_', 122, ',', 286, ',', 220, ',', 1128, '']

    :returns: a list where numbers in string `s` are converted to ints for comparison. non-number characters are kept as strings
    """
    return [int(part) if part.isdigit() else part for part in re.split("(\d+)", s)]


def gen_img_ref(img, coord):
    return f"{img.split('.')[0]}_{coord}"


def get_summary(elements):
    if len(elements) == 0:
        return f"<span class='faded'>{'Empty' if APP_LANG == 'en' else 'Vide'}</span>"

    strings = [str(el) for el in elements]
    if len(strings) < 4:
        return "<br>".join(strings)

    first_three, rest = strings[:3], strings[3:]
    ellip = ""  # "<span class='ellipsis'>...</span>"

    visible = "<br>".join(first_three)
    summary = f"<summary>{visible}<br>{ellip}</summary>"
    details = "<br>".join(rest)
    return f"<details class='summary'>{summary}{details}</details>"


def is_in_group(creator, current_user):
    groups = list(creator.groups.all())
    return current_user.groups.filter(name__in=groups).exists()


def parse_img_ref(img_string):
    # wit<id>_<digit><id>_<canvas_nb>_<x>,<y>,<h>,<w>.jpg
    wit, digit, canvas, coord = img_string.split("_")
    return {
        "wit": extract_nb(wit),
        "digit": extract_nb(digit),
        "canvas": canvas,
        "coord": coord.split(".")[0].split(","),
    }


def cast(val, to_type):
    if val is None:
        return None
    try:
        return to_type(val)
    except (ValueError, TypeError):
        if to_type == int:
            return 0
        elif to_type == float:
            return 0.0
        return None
