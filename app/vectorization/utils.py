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


def get_annotation_urls(anno: Regions):
    """
    {
        "wit1_man191_0009_166,1325,578,516": ""https://eida.obspm.fr/iiif/2/wit1_man191_0009.jpg/166,1325,578,516/full/0/default.jpg"",
        "wit1_man191_0027_1143,2063,269,245": "https://eida.obspm.fr/iiif/2/wit1_man191_0027.jpg/1143,2063,269,245/full/0/default.jpg",
        "wit1_man191_0031_857,2013,543,341": "https://eida.obspm.fr/iiif/2/wit1_man191_0031.jpg/857,2013,543,341/full/0/default.jpg",
        "img_name": "..."
    }
    """
    folio_anno = []

    _, canvas_annos = formatted_annotations(anno)
    for canvas_nb, annos, img_name in canvas_annos:
        if len(annos):
            folio_anno.append(
                {
                    gen_img_ref(img_name, a[0]): gen_iiif_url(
                        img_name, 2, f"{a[0]}/full/0"
                    )
                    for a in annos
                }
            )

    return flatten_dict(folio_anno)


def vectorization_request_for_one(anno):

    """
    Request to the API to launch vectorization on one witness
    """

    try:
        response = requests.post(
            url=f"{CV_API_URL}/vectorization/start",
            json={
                "doc_id": anno.get_ref(),
                "model": f"{VECTO_MODEL_EPOCH}",
                "images": get_annotation_urls(anno),
                "callback": f"{APP_URL}/{APP_NAME}/receive-vecto",
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
                "error_message": f"Request failed for {anno} with status code: {response.status_code}",
                "request_info": {
                    "method": "POST",
                    "url": f"{CV_API_URL}/vectorization/start",
                    "payload": {
                        "document": anno,
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
        log(f"[vectorization_request] Request failed for {anno}", e)
        return False


def vectorization_request(annos):

    """
    Request to the API to launch vectorization on several witnesses
    """

    for anno in annos:
        success = vectorization_request_for_one(anno)
        if success:
            return True
    return False


def delete_and_relauch_request(anno):

    """
    Request to the API endpoint to delete imgs from the repo corresponding to doc_id + relauch the vectorization
    """

    try:
        response = requests.post(
            url=f"{CV_API_URL}/vectorization/delete_and_relaunch",
            json={
                "doc_id": anno.get_ref(),
                "model": f"{VECTO_MODEL_EPOCH}",
                "images": get_annotation_urls(anno),
                "callback": f"{APP_URL}/{APP_NAME}/receive-vecto",
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
                "error_message": f"Request failed for {anno} with status code: {response.status_code}",
                "request_info": {
                    "method": "POST",
                    "url": f"{CV_API_URL}/vectorization/delete_and_relauch",
                    "payload": {
                        "document": anno,
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
        log(f"[vectorization_request] Request failed for {anno}", e)
        return False
