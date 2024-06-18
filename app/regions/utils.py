import requests

from app.config.settings import CV_API_URL, APP_URL, APP_NAME
from app.webapp.models.digitization import Digitization
from app.webapp.models.treatment import Treatment
from app.regions.const import EXTRACTOR_MODEL
from app.webapp.utils.logger import log


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
            url=f"{CV_API_URL}/extraction/start",
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
                    "url": f"{CV_API_URL}/extraction/start",
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
    if not CV_API_URL.startswith("http"):
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
