import re
import requests

from app.config.settings import (
    EXAPI_URL,
    EXTRACTOR_MODEL,
    APP_URL,
    APP_NAME,
    CANTALOUPE_APP_URL,
)
from app.webapp.models.digitization import Digitization
from app.webapp.models.regions import Regions
from app.webapp.models.treatment import Treatment

from app.webapp.utils.logger import log
from app.webapp.utils.paths import REGIONS_PATH


def create_treatment(treatment_type, task_type, user_id, treated_object):
    try:
        treatment = Treatment(
            treatment_type=treatment_type,
            task_type=task_type,
            user_id=user_id,
            treated_object=treated_object,
        )
        treatment.save()

        return treatment
    except Exception as e:
        log(
            f"[create_treatment] Failed to create treatment requested by user {user_id} for digit #{treated_object.id}",
            e,
        )
        return False


def regions_request(digit: Digitization, user_id, treatment_type="auto"):
    treatment = create_treatment(
        treatment_type=treatment_type,
        task_type="regions",
        user_id=user_id,
        treated_object=digit,
    )

    try:
        response = requests.post(
            url=f"{EXAPI_URL}/extraction/start",
            data={
                "experiment_id": treatment.id,
                "manifest_url": digit.gen_manifest_url(),
                "model": f"{EXTRACTOR_MODEL}",  # Use only if specific model is desire
                "callback": f"{APP_URL}/{APP_NAME}/get-regions",  # URL to which the regions file must be sent back
            },
        )
        if response.status_code == 200:
            treatment.update_treatment()
            log(
                f"[regions_request] Regions extraction request send: {response.text or ''}"
            )
            return True
        else:
            error = {
                "source": "[regions_request]",
                "error_message": f"Regions extraction request for {digit.get_ref()} with status code: {response.status_code}",
                "request_info": {
                    "method": "POST",
                    "url": f"{EXAPI_URL}/extraction/start",
                    "data": {
                        "manifest_url": digit.gen_manifest_url(),
                        "model": f"{EXTRACTOR_MODEL}",
                        "callback": f"{APP_URL}/{APP_NAME}/get-regions",
                    },
                },
                "response_info": {
                    "status_code": response.status_code,
                    "text": response.text or "",
                },
            }

            treatment.error_treatment(error)
            log(error)
            return False
    except Exception as e:
        treatment.error_treatment(e)
        log(
            f"[regions_request] Regions extraction request for {digit.get_ref()} failed",
            e,
        )
        return False


def send_regions_request(digits, user_id):
    if not EXAPI_URL.startswith("http"):
        # on local to prevent bugs
        return True

    for digit in digits:
        try:
            regions_request(digit, user_id)
        except Exception as e:
            log(
                f"[send_regions_request] Failed to send regions extraction request for digit #{digit.id}",
                e,
            )
            return False
    return True


def get_txt_regions(regions: Regions):
    try:
        with open(f"{REGIONS_PATH}/{regions.get_ref()}.txt") as f:
            return [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        return None


def get_regions_img(regions: Regions):
    lines = get_txt_regions(regions)
    if lines is None:
        return []

    imgs = []
    img_name = f"{regions.get_ref()}_0000.jpg"
    for line in lines:
        if len(line.split()) == 2:
            img_name = line.split()[1]
        else:
            x, y, w, h = line.split()
            imgs.append(
                f"{CANTALOUPE_APP_URL}/iiif/2/{img_name}/{x},{y},{w},{h}/full/0/default.jpg"
            )
    return imgs


def create_empty_regions(digit: Digitization):
    imgs = digit.get_imgs()
    if len(imgs) == 0:
        return False

    try:
        regions = Regions(digitization=digit, model="Manual")
        regions.save()
    except Exception as e:
        log(
            f"[create_empty_regions] Unable to create new Regions for digit #{digit.id} in the database",
            e,
        )
        return False

    try:
        with open(f"{REGIONS_PATH}/{regions.get_ref()}.txt", "w") as regions_file:
            for i, img_name in enumerate(imgs, 1):
                regions_file.write(f"{i} {img_name}\n")
    except Exception as e:
        log(
            f"[create_empty_regions] unable to create new Regions file for digit #{digit.id}",
            e,
        )

    return regions


def check_regions_file(file_content):
    # Either contains a number then an img.jpg / Or a series of 4 numbers
    pattern = re.compile(r"^\d+\s+\S+\.jpg$|^\d+\s\d+\s\d+\s\d+$")
    for line in file_content.split("\n"):
        if line == "":
            continue
        if not pattern.match(line):
            log(f"[check_regions_file] incorrect line {line}")
            return False
    return True
