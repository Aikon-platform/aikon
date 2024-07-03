import requests

from app.config.settings import APP_URL, APP_NAME, CV_API_URL
from app.vectorization.const import VECTO_MODEL_EPOCH

from app.webapp.utils.logger import log
from app.webapp.utils.iiif.annotation import get_regions_urls


def make_vectorization_request(regions, endpoint):
    """
    Function to make a vectorization request to the specified endpoint.
    """
    try:
        url = f"{CV_API_URL}/vectorization/{endpoint}"
        payload = {
            "doc_id": regions.get_ref(),
            "model": f"{VECTO_MODEL_EPOCH}",
            "images": get_regions_urls(regions),
            "callback": f"{APP_URL}/{APP_NAME}/receive-vectorization",
        }

        response = requests.post(url, json=payload)

        print("Response:", response)
        print("Response status code:", response.status_code)
        print("Response text:", response.text)

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
                    "url": url,
                    "payload": payload,
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


def vectorization_request_for_one(regions):

    """
    Request to the API to launch vectorization on one witness
    """

    return make_vectorization_request(regions, "start")


def vectorization_request(regions):

    """
    Request to the API to launch vectorization on several witnesses
    """

    for region in regions:
        success = vectorization_request_for_one(region)
        if success:
            return True
    return False


def delete_and_relauch_request(regions):

    """
    Request to the API endpoint to delete imgs from the repo corresponding to doc_id + relauch the vectorization
    """

    return make_vectorization_request(regions, "delete_and_relaunch")
