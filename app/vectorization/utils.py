import os
import zipfile

import requests

from app.config.settings import APP_URL, APP_NAME, CV_API_URL, APP_LANG
from app.vectorization.const import VECTO_MODEL_EPOCH, SVG_PATH
from app.webapp.models.regions import Regions
from app.webapp.models.utils.constants import WIT

from app.webapp.utils.logger import log
from app.webapp.utils.iiif.annotation import get_regions_urls


def prepare_request(witnesses, treatment_id):
    regions_list = []
    regions_dic = {}

    try:
        log(
            f"[prepare_request] Start preparing vectorization request for treatment_id: {treatment_id}"
        )

        for witness in witnesses:
            log(f"[prepare_request] Checking vectorizations for witness: {witness.id}")
            if witness.check_vectorizations():
                log(
                    f"[prepare_request] All regions for witness {witness.id} have already been processed and vectorized"
                )
                return {
                    "message": f"All the regions of the {WIT} have already been processed and vectorized."
                    if APP_LANG == "en"
                    else f"Toutes les régions du {WIT} sont vectorisées."
                }
            else:
                log(f"[prepare_request] Retrieving regions for witness: {witness.id}")
                regions_list.extend(witness.get_regions())

        if regions_list:
            log(f"[prepare_request] Found {len(regions_list)} regions to process.")
            for regions in regions_list:
                log(f"[prepare_request] Processing region: {regions.get_ref()}")
                regions_dic.update({regions.get_ref(): get_regions_urls(regions)})

            log(
                f"[prepare_request] Successfully prepared vectorization request for treatment_id: {treatment_id}"
            )
            return {
                "experiment_id": f"{treatment_id}",
                "documents": regions_dic,
                "model": f"{VECTO_MODEL_EPOCH}",
                "callback": f"{APP_URL}/{APP_NAME}/get-vectorization",  # URL to which the SVG zip file must be sent back
                "tracking_url": f"{APP_URL}/{APP_NAME}/api-progress",
            }

        else:
            log(
                f"[prepare_request] No regions found to vectorize for any of the selected witnesses"
            )
            return {
                "message": f"No regions to vectorize for all the selected {WIT}es"
                if APP_LANG == "en"
                else f"Pas de régions à vectoriser pour tous les {WIT}s sélectionnés"
            }

    except Exception as e:
        log(
            f"[prepare_request] Failed to prepare data for vectorization request. Error: {str(e)}"
        )
        raise Exception(
            f"[prepare_request] Failed to prepare data for vectorization request. Error: {str(e)}"
        )


def vectorization_request_for_one(regions):
    """
    To relaunch vectorization request for one witness in case the automatic process has failed
    """
    try:
        response = requests.post(
            url=f"{CV_API_URL}/vectorization/start",
            json={
                "doc_id": regions.get_ref(),
                "model": f"{VECTO_MODEL_EPOCH}",
                "images": get_regions_urls(regions),
                "callback": f"{APP_URL}/{APP_NAME}/get-vectorization",
            },
        )
        if response.status_code == 200:
            log(
                f"[vectorization_request] Vectorization request sent: {response.text or ''}"
            )
            return True
        else:
            error = {
                "source": "[vectorization_request]",
                "error_message": f"Request failed for {regions} with status code: {response.status_code}",
                "request_info": {
                    "method": "POST",
                    "url": f"{CV_API_URL}/vectorization/start",
                    "payload": {
                        "document": regions,
                        "callback": f"{APP_URL}/{APP_NAME}/get-vectorization",
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
        log(f"[vectorization_request] Request failed for {regions}", e)
        raise Exception(f"[vectorization_request] Request failed for {regions}")


def delete_and_relauch_request(regions):
    """
    Request to the API endpoint to delete imgs from the repo corresponding to doc_id + relaunch the vectorization
    """
    try:
        response = requests.post(
            url=f"{CV_API_URL}/vectorization/start",
            json={
                "doc_id": regions.get_ref(),
                "model": f"{VECTO_MODEL_EPOCH}",
                "images": get_regions_urls(regions),
                "callback": f"{APP_URL}/{APP_NAME}/get-vectorization",
            },
        )
        if response.status_code == 200:
            log(
                f"[vectorization_request] Vectorization request sent: {response.text or ''}"
            )
            return True
        else:
            error = {
                "source": "[vectorization_request]",
                "error_message": f"Request failed for {regions} with status code: {response.status_code}",
                "request_info": {
                    "method": "POST",
                    "url": f"{CV_API_URL}/vectorization/delete_and_relauch",
                    "payload": {
                        "document": regions,
                        "callback": f"{APP_URL}/{APP_NAME}/get-vectorization",
                    },
                },
                "response_info": {
                    "status_code": response.status_code,
                    "text": response.text or "",
                },
            }

            log(error)
            return False
    except Exception as e:
        log(f"[vectorization_request] Request failed for {regions}", e)
        return False


def save_svg_files(zip_file):
    """
    Extracts SVG files from a ZIP file and saves them to the SVG_PATH directory.
    """
    # Vérifie si le répertoire SVG_PATH existe, sinon le crée
    if not os.path.exists(SVG_PATH):
        os.makedirs(SVG_PATH)

    try:
        with zipfile.ZipFile(zip_file, "r") as zip_ref:
            for file_info in zip_ref.infolist():
                # Vérifie si le fichier est un fichier SVG
                if file_info.filename.endswith(".svg"):
                    file_path = os.path.join(
                        SVG_PATH, os.path.basename(file_info.filename)
                    )

                    # Supprime le fichier existant s'il y en a un
                    if os.path.exists(file_path):
                        os.remove(file_path)

                    # Extrait le fichier SVG et l'écrit dans le répertoire spécifié
                    with zip_ref.open(file_info) as svg_file:
                        with open(file_path, "wb") as output_file:
                            output_file.write(svg_file.read())
    except Exception as e:
        log(f"[save_svg_files] Error when extracting SVG files from ZIP file", e)
        return False
    return True


def reset_vectorization(regions: Regions):
    regions_id = regions.id
    try:
        regions_ref = regions.get_ref()
    except Exception as e:
        log(
            f"[reset_vectorization] Failed to retrieve region ref for id {regions_id}",
            e,
        )
        return False

    for file in os.listdir(SVG_PATH):
        # TODO change here once SVG files will be stored in different folders
        if regions_ref in file:
            try:
                os.remove(os.path.join(SVG_PATH, file))
            except OSError as e:
                log(f"[reset_vectorization] Error removing {file}", e)

    # TODO send request to delete svg to API
    return True
