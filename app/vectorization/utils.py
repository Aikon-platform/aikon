import requests
from app.config.settings import APP_URL, APP_NAME, CV_API_URL
from app.vectorization.config import VECTO_MODEL_EPOCH
from app.webapp.models.regions import Regions
from app.webapp.utils.functions import flatten_dict
from app.webapp.utils.iiif import gen_iiif_url
from app.webapp.utils.iiif.annotation import formatted_annotations
from app.webapp.utils.logger import log


def gen_img_ref(img, coord):
    return f"{img.split('.')[0]}_{coord}"


def get_regions_urls(regions: Regions):
    """
    {
        "wit1_man191_0009_166,1325,578,516": ""https://eida.obspm.fr/iiif/2/wit1_man191_0009.jpg/166,1325,578,516/full/0/default.jpg"",
        "wit1_man191_0027_1143,2063,269,245": "https://eida.obspm.fr/iiif/2/wit1_man191_0027.jpg/1143,2063,269,245/full/0/default.jpg",
        "wit1_man191_0031_857,2013,543,341": "https://eida.obspm.fr/iiif/2/wit1_man191_0031.jpg/857,2013,543,341/full/0/default.jpg",
        "img_name": "..."
    }
    """
    folio_annotations = []

    _, canvas_annotations = formatted_annotations(regions)
    for canvas_nb, annotations, img_name in canvas_annotations:
        if len(annotations):
            folio_annotations.append(
                {
                    gen_img_ref(img_name, a[0]): gen_iiif_url(
                        img_name, 2, f"{a[0]}/full/0"
                    )
                    for a in annotations
                }
            )

    return flatten_dict(folio_annotations)


def vectorization_request_for_one(regions):

    """
    Request to the API to launch vectorization on one witness
    """

    try:
        response = requests.post(
            url=f"{CV_API_URL}/vectorization/start",
            json={
                "doc_id": regions.get_ref(),
                "model": f"{VECTO_MODEL_EPOCH}",
                "images": get_regions_urls(regions),
                "callback": f"{APP_URL}/{APP_NAME}/receive-vectorization",
            },
        )

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
                    "url": f"{CV_API_URL}/vectorization/start",
                    "payload": {
                        "document": regions,
                        "callback": f"{APP_URL}/{APP_NAME}/vectorization",
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

    try:
        response = requests.post(
            url=f"{CV_API_URL}/vectorization/start",
            json={
                "doc_id": regions.get_ref(),
                "model": f"{VECTO_MODEL_EPOCH}",
                "images": get_regions_urls(regions),
                "callback": f"{APP_URL}/{APP_NAME}/receive-vectorization",
            },
        )

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
                    "url": f"{CV_API_URL}/vectorization/delete_and_relauch",
                    "payload": {
                        "document": regions,
                        "callback": f"{APP_URL}/{APP_NAME}/vectorization",
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
