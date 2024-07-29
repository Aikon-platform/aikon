import os
import zipfile

import requests

from app.config.settings import APP_URL, APP_NAME, CV_API_URL, APP_LANG
from app.vectorization.const import VECTO_MODEL_EPOCH, SVG_PATH
from app.webapp.models.utils.constants import WIT

from app.webapp.utils.logger import log
from app.webapp.utils.iiif.annotation import get_regions_urls


def prepare_request(witnesses, treatment_id):
    regions_list = []
    regions_dic = {}

    try:
        for witness in witnesses:
            if witness.has_vectorization():
                log(
                    f"[vectorization_request] Witness {witness.get_ref()} already has vectorizations"
                )
                pass
            else:
                regions_list.extend(witness.get_regions())

        if regions_list:
            for regions in regions_list:
                regions_dic.update({regions.get_ref(): get_regions_urls(regions)})

            return {
                "experiment_id": f"{treatment_id}",
                "documents": regions_dic,
                "model": f"{VECTO_MODEL_EPOCH}",
                "callback": f"{APP_URL}/{APP_NAME}/get-vectorization",  # URL to which the SVG zip file must be sent back
                "tracking_url": f"{APP_URL}/{APP_NAME}/api-progress",
            }

        else:
            return {
                "message": f"No regions to vectorize for all the selected {WIT}es"
                if APP_LANG == "en"
                else f"Pas de regions à vectoriser pour tous les {WIT}s sélectionnés"
            }

    except Exception as e:
        log(
            f"[prepare_request] Failed to prepare data for vectorization request",
            e,
        )
        raise Exception(
            f"[prepare_request] Failed to prepare data for vectorization request"
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
    Request to the API endpoint to delete imgs from the repo corresponding to doc_id + relauch the vectorization
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
                # TODO do not save jpg file
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
