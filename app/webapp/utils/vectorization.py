from .similarity import *
import hashlib
import os
from itertools import combinations_with_replacement
import numpy as np

import requests
from typing import List

from app.config.settings import EXAPI_URL, APP_URL, APP_NAME, VECTO_MODEL_EPOCH
from app.webapp.models.annotation import Annotation
from app.webapp.utils.functions import flatten_dict
from app.webapp.utils.iiif import gen_iiif_url
from app.webapp.utils.iiif.annotation import formatted_annotations
from app.webapp.utils.logger import log
from app.webapp.utils.paths import SCORES_PATH


def vectorization_request(annos):

    for anno in annos:
        try:
            response = requests.post(
                url=f"{EXAPI_URL}/vectorization/start",
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
                    f"[vectorization_request] Vectorization request send: {response.text or ''}"
                )
                return True
            else:
                error = {
                    "source": "[vectorization_request]",
                    "error_message": f"Request failed for {anno} with status code: {response.status_code}",
                    "request_info": {
                        "method": "POST",
                        "url": f"{EXAPI_URL}/vectorization/start",
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


def vectorization_request_for_one(anno):

    try:
        response = requests.post(
            url=f"{EXAPI_URL}/vectorization/start",
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
                f"[vectorization_request] Vectorization request send: {response.text or ''}"
            )
            return True
        else:
            error = {
                "source": "[vectorization_request]",
                "error_message": f"Request failed for {anno} with status code: {response.status_code}",
                "request_info": {
                    "method": "POST",
                    "url": f"{EXAPI_URL}/vectorization/start",
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
