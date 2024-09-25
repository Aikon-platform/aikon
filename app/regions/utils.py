import requests

from app.config.settings import CV_API_URL, APP_URL, APP_NAME, APP_LANG

from app.regions.const import EXTRACTOR_MODEL
from app.webapp.models.utils.constants import WIT
from app.webapp.utils.iiif.annotation import get_regions_annotations
from app.webapp.utils.logger import log


def prepare_request(witnesses, treatment_id):
    manifests = {}

    try:
        for witness in witnesses:
            if witness.has_regions():
                regions = witness.get_regions()
                wit_ref = witness.get_ref()

                # check if the is annotations in SAS for this witness
                anno_regions = {}
                for region in regions:
                    anno_regions = get_regions_annotations(
                        region, as_json=True, r_annos=anno_regions
                    )

                if len(anno_regions) != 0:
                    log(f"[prepare_request] Witness {wit_ref} already has regions")
                    continue

                different_model = True
                for region in regions:
                    if region.model == EXTRACTOR_MODEL:
                        different_model = False
                        break

                if not different_model:
                    log(
                        f"[prepare_request] Witness {wit_ref} already has regions extracted with {EXTRACTOR_MODEL}"
                    )
                    continue

            digits = witness.get_digits()
            for digit in digits:
                manifests.update({witness.get_ref(): digit.gen_manifest_url()})

        if manifests:
            return {
                "experiment_id": f"{treatment_id}",
                "documents": manifests,
                "model": f"{EXTRACTOR_MODEL}",  # Use only if specific model is desired
                "callback": f"{APP_URL}/{APP_NAME}/get-regions",  # URL to which the regions file must be sent back
                "tracking_url": f"{APP_URL}/{APP_NAME}/api-progress",
            }
        else:
            return {
                "message": f"Regions were already extracted for all the selected {WIT}es"
                if APP_LANG == "en"
                else f"Les régions ont déjà été extraites pour tous les {WIT}s sélectionnés"
            }

    except Exception as e:
        log(
            f"[prepare_request] Failed to prepare data for regions request",
            e,
        )
        raise Exception(f"[prepare_request] Failed to prepare data for regions request")


def regions_request(manifests, treatment_id):
    """
    To relaunch extraction request in case the automatic process has failed
    """

    try:
        response = requests.post(
            url=f"{CV_API_URL}/regions/start",
            json={
                "manifests": manifests,
                "experiment_id": f"{treatment_id}",
                "model": f"{EXTRACTOR_MODEL}",  # Use only if specific model is desire
                "callback": f"{APP_URL}/{APP_NAME}/get-regions",  # URL to which the regions file must be sent back
            },
        )
        if response.status_code == 200:
            api_response = response.json()
            log(
                f"[regions_request] Regions extraction request send: {api_response or ''}"
            )
            return api_response["tracking_id"]
        else:
            error = {
                "source": "[regions_request]",
                "error_message": f"Regions extraction request for treatment #{treatment_id} with status code: {response.status_code}",
                "request_info": {
                    "method": "POST",
                    "url": f"{CV_API_URL}/regions/start",
                    "payload": {
                        "manifests": manifests,
                        "treatment": treatment_id,
                        "model": f"{EXTRACTOR_MODEL}",
                        "callback": f"{APP_URL}/{APP_NAME}/get-regions",
                    },
                },
                "response_info": {
                    "status_code": response.status_code,
                    "text": response.text or "",
                },
            }

            log(error)
            raise Exception(error)
    except Exception as e:
        log(
            f"[regions_request] Regions extraction request for treatment #{treatment_id} failed",
            e,
        )
        raise Exception(
            f"[regions_request] Regions extraction request for treatment #{treatment_id} failed"
        )
