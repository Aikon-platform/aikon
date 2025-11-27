import importlib
import json
from typing import List, Tuple

import requests
from django.contrib.auth.models import User

from app.config.settings import BASE_URL, APP_NAME, API_URL, APP_LANG
from app.webapp.models.digitization import Digitization
from app.webapp.models.document_set import DocumentSet
from app.webapp.models.regions import Regions
from app.webapp.models.witness import Witness
from app.webapp.utils.logger import log


def get_user(user: User = None) -> User:
    if not user:
        try:
            user = User.objects.filter(is_superuser=True).first()
        except Exception as e:
            log(
                f"[create_doc_set] Unable to retrieve admin user",
                e,
            )
            raise e
    return user


def create_doc_set(
    doc_list: list | dict, user: User = None
) -> Tuple[DocumentSet, bool]:
    if not len(doc_list):
        log(
            f"[create_doc_set] Failed to create Document Set from empty list of documents",
        )
        raise Exception("No documents to create Document Set")

    user = get_user(user)
    if type(doc_list) == dict:
        return create_doc_set_from_ids(doc_list, user)
    return create_doc_set_from_records(doc_list, user)


def create_doc_set_from_records(
    records: List[Witness | Digitization | Regions], user: User = None
):
    wit_ids = set()
    doc_title = "Document set"
    is_new = False
    user = get_user(user)

    try:
        for record in records:
            witness = record.get_witness() if hasattr(record, "get_witness") else record
            # TODO: do not put all documents as witnesses, because some could be series, etc.
            wit_ids.add(witness.id if witness else None)
            if len(records) == 1:
                doc_str = witness.__str__()
                doc_title = doc_str if len(doc_str) < 48 else f"{doc_str[:48]}…"
    except Exception as e:
        log(
            f"[create_doc_set] Failed to retrieve witness ids",
            e,
        )
        raise e

    try:
        wit_ids = list(sorted(wit_ids))
        # check if there is a doc set with same wit_ids and user
        doc_set = DocumentSet.objects.filter(user=user, wit_ids=wit_ids).first()

        if not doc_set:
            # if not create one
            doc_set = DocumentSet.objects.create(
                title=doc_title,
                user=user,
                wit_ids=wit_ids,
                is_public=False,
            )
            doc_set.save()
            is_new = True
    except Exception as e:
        log(
            f"[create_doc_set] Failed to create Document Set for witnesses {wit_ids}",
            e,
        )
        raise e

    return doc_set, is_new


def create_doc_set_from_ids(ids: dict, user: User = None):
    """
    ids: {
        "wit_ids": List[int],
        "ser_ids": List[int],
        "digit_ids": List[int],
        "work_ids": List[int],
    }
    """
    is_new = False
    user = get_user(user)
    try:
        doc_set = DocumentSet.objects.filter(user=user, **ids).first()
        if not doc_set:
            doc_set = DocumentSet.objects.create(
                title="Document set",
                user=user,
                **ids,
                is_public=False,
            )
            doc_set.save()
            is_new = True
    except Exception as e:
        log(
            f"[create_doc_set] Failed to create Document Set for witnesses {ids}",
            e,
        )
        raise e

    return doc_set, is_new


def create_treatment(
    records: List[Witness | Digitization | Regions], task_name, user: User = None
) -> int:
    user = get_user(user)
    doc_set, is_new = create_doc_set(records, user)

    try:
        from app.webapp.models.treatment import Treatment

        treatment = Treatment.objects.create(
            requested_by=user,
            task_type=task_name,
            document_set=doc_set,
        )
        treatment.save()
    except Exception as e:
        log(
            f"[create_treatment] Failed to create Treatment for document set #{doc_set.id}",
            e,
        )
        raise e

    return True


def process_task_results(task_name, data, completed=True):
    try:
        module = importlib.import_module(f"{task_name}.utils")
        return getattr(module, "process_results")(data, completed)
    except (ImportError, AttributeError) as e:
        raise e


def prepare_task_request(task_name, records, treatment_id):
    try:
        module = importlib.import_module(f"{task_name}.utils")
        return getattr(module, "prepare_request")(records, treatment_id)
    except (ImportError, AttributeError) as e:
        raise e


def task_request(task_name, records, treatment_id=None, endpoint="start"):
    """
    Utility function to send a vectorization request to a specified endpoint.
    """
    if not treatment_id:
        try:
            # create treatment post save method triggers the task request
            create_treatment(records, task_name)
            return True
        except Exception:
            treatment_id = "manual"

    # TODO probably useless => put in start task method?
    try:
        payload = prepare_task_request(task_name, records, treatment_id)
        response = requests.post(url=f"{API_URL}/{task_name}/start", json=payload)
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
                    "url": f"{API_URL}/{task_name}/{endpoint}",
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
            documents.extend(prepare_document(record, **parameters))

        if documents:
            uids = [d.get("uid", "UID") for d in documents]
            log(
                f"[prepare_request] Found {len(documents)} documents to process: {', '.join(uids)}"
            )

            return {
                "experiment_id": str(treatment_id),
                "documents": documents,
                # URL to which results and task notifications are sent back
                "notify_url": f"{BASE_URL}/{APP_NAME}/{task_name}/notify",
                **parameters,
            }

        err = (
            f"No document to process in the selected records"
            if APP_LANG == "en"
            else f"Aucun document à traiter pour les enregistrements sélectionnés."
        )
        log(f"[prepare_request] {err}")
        raise Exception(err)

    except Exception as e:
        log("[prepare_request] Failed to prepare request", e)
        raise e


def receive_notification(request):
    """
    :param request:
    :return: json response, status code.
    """
    from app.webapp.models.treatment import Treatment

    if request.method != "POST":
        return {"success": False, "error": "Only POST requests are supported"}, 400

    try:
        data = json.loads(request.body.decode("utf-8"))
        assert data is not None
        assert "experiment_id" in data
        assert "event" in data
    except (ValueError, AssertionError) as e:
        return {
            "success": False,
            "error": f"Data payload does not contain expected content: {e}",
        }, 400

    try:
        treatment = Treatment.objects.get(id=data["experiment_id"])
    except Treatment.DoesNotExist:
        # TODO handle manual treatment?
        return {"success": False, "error": "Treatment not found"}, 400

    try:
        treatment.receive_notification(event=data.get("event"), data=data)
    except Exception as e:
        log("[receive_notification] Error processing API response", e)
        return {"success": False, "error": f"Error processing response {e}"}, 400

    return {"success": True, "message": "Update received"}, 200
