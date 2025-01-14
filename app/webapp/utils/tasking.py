import importlib
from typing import List

import requests

from app.config.settings import APP_URL, APP_NAME, CV_API_URL, APP_LANG
from app.webapp.models.digitization import Digitization
from app.webapp.models.regions import Regions
from app.webapp.models.witness import Witness
from app.webapp.utils.logger import log


def create_treatment(records: List[Witness | Digitization | Regions]):
    # TODO : is it better to create a Treatment and let the post save do the work (better tracking)
    # TODO : or use task_request separately (better control)
    # TODO : consider changing tasking workflow (it is weird to trigger start_task in get_all_witnesses task)
    return "manual"


def task_payload(task_name, records, treatment_id):
    try:
        module = importlib.import_module(f"{task_name}.utils")
        return getattr(module, "prepare_request")(records, treatment_id)
    except (ImportError, AttributeError) as e:
        raise e


def task_request(task_name, records, treatment_id=None, endpoint="start"):
    """
    Utility function to send a vectorization request to a specified endpoint.
    """
    if treatment_id:
        treatment_id = create_treatment(records)

    try:
        payload = task_payload(task_name, records, treatment_id)
        response = requests.post(url=f"{CV_API_URL}/{task_name}/start", json=payload)
        if response.status_code == 200:
            log(
                f"[{task_name}_request] Successfully sent request: {response.text or ''}"
            )
            return True
        else:
            error = {
                "source": f"[{task_name}_request]",
                "error_message": f"Request failed with status code: {response.status_code}",
                "request_info": {
                    "method": "POST",
                    "url": f"{CV_API_URL}/{task_name}/{endpoint}",
                    "payload": payload,
                },
                "response_info": {
                    "status_code": response.status_code,
                    "text": response.text or "",
                },
            }
            log(error)
            raise Exception(error)
    except Exception as e:
        log(f"[{task_name}_request] Request for Treatment #{treatment_id} failed", e)
        raise e


def prepare_request(records, treatment_id, prepare_document, task_name, parameters={}):
    """
    Generalized function to prepare requests by processing records and generating documents.

    Args:
        records (list): List of records to process (Witnesses, Digitization, Regions)
        treatment_id (str): ID of the treatment.
        prepare_document (callable): Function to process a witness and return relevant data.
        task_name (str): app name of the corresponding task module
        parameters (dict): Additional parameters to be added in request payload

    Returns:
        dict: Prepared request data or message.
    """
    try:
        log(f"[prepare_request] Start preparing request for Treatment #{treatment_id}")

        documents = []
        for record in records:
            documents.extend(prepare_document(record, parameters))

        if documents:
            log(f"[prepare_request] Found {len(documents)} documents to process.")

            return {
                "experiment_id": treatment_id,
                "documents": documents,
                # URL to which results and task notifications are sent back
                "notify_url": f"{APP_URL}/{APP_NAME}/{task_name}/notify",
                **parameters,
            }

        log("[prepare_request] No document to process in selected records.")
        return {
            "message": f"No document to process in the selected records"
            if APP_LANG == "en"
            else f"Aucun document à traiter pour les enregistrements sélectionnés."
        }

    except Exception as e:
        log("[prepare_request] Failed to prepare request", e)
        raise e
