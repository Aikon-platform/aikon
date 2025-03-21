import re
import requests

from app.regions.const import EXTRACTOR_MODEL
from app.regions.tasks import process_regions_file
from app.webapp.models.digitization import Digitization
from app.webapp.models.regions import Regions
from app.webapp.models.witness import Witness
from app.webapp.utils import tasking
from app.webapp.utils.iiif import parse_ref
from app.webapp.utils.iiif.annotation import has_annotation
from app.webapp.utils.logger import log
from config.settings import APP_LANG


################################################################
# ⚠️   prepare_request() & process_results() are mandatory  ⚠️ #
# ⚠️ function used by Treatment to generate request payload ⚠️ #
# ⚠️    and save results files when sends back by the API   ⚠️ #
################################################################


def prepare_request(witnesses, treatment_id):
    return tasking.prepare_request(
        witnesses,
        treatment_id,
        prepare_document,
        "regions",
        {"model": f"{EXTRACTOR_MODEL}"},
    )


def process_results(data, completed=True):
    """
    :param data: {
        "output": {
            ?"dataset_url": dataset_url,
            ?"results_url":  [{
                "doc_id": doc_id,
                "result_url": result_url  => result_url returns a downloadable JSON
            }, {...}],
            "error": [list of error message],
        }
    }
    :param completed: whether the treatment is achieved or these are intermediary results
    result_url content
    [{
        "source": "image_name.jpg",
        "width": 1912,
        "height": 2500,
        "crops": [
          {
            "bbox": "gb638390",
            "crop_id": "image_name.jpg-gb638390",
            "source": "image_name.jpg",
            "confidence": 0.8001,
            "absolute": {
              "x1": 866, "y1": 422, "x2": 1295, "y2": 1048, "width": 429, "height": 626
            },
            "relative": {
              "x1": 0.4529, "y1": 0.1688, "x2": 0.6773, "y2": 0.4192, "width": 0.2244, "height": 0.2504
            }
          },
          {...}
        ],
        "doc_uid": "doc_ref"
      },{...}]
    :return:
    """
    output = data.get("output", None)
    if not data or not output:
        log("No extraction results to process")
        return

    results_url = output.get("results_url", None)
    if not results_url:
        error = output.get("error", ["No extraction results to process"])
        log(error)
        raise ValueError("\n".join(error))

    # doc_results is supposed to be { "doc_id": doc_id, "result_url": result_url }
    for doc_results in results_url:
        doc_id = doc_results.get("doc_id")
        result_url = doc_results.get("result_url")

        digit_id = parse_ref(doc_id)["digit"][1]
        try:
            response = requests.get(result_url, stream=True)
            response.raise_for_status()
            json_content = response.json()
        except Exception as e:
            log(f"Could not retrieve annotation from {result_url}", e)
            continue

        if not check_regions_json_file(json_content):
            continue

        try:
            model_name = result_url.split("/")[-1].split("+")[0] or EXTRACTOR_MODEL
            process_regions_file.delay(json_content, digit_id, model_name)
        except Exception as e:
            log(f"Could not process annotation from {result_url}", e)
            raise e
    return


def prepare_document(document: Witness | Digitization | Regions, **kwargs):
    if not type(document).__name__ == "Witness" and not document.has_images():
        raise ValueError(
            f"“{document}” has no digitization to extract regions from"
            if APP_LANG == "en"
            else f"« {document} » n'a pas de numérisation pour laquelle extraire des régions"
        )

    regions = document.get_regions() if hasattr(document, "get_regions") else [document]

    if any(
        region.model == kwargs["model"] and has_annotation(region.get_ref())
        for region in regions
    ):
        raise ValueError(
            f"“{document}” already has regions extracted with {kwargs['model']}"
            if APP_LANG == "en"
            else f"« {document} » a déjà des régions extraites avec {kwargs['model']}"
        )

    digits = document.get_digits() if hasattr(document, "get_digits") else [document]

    return [
        {"type": "iiif", "src": digit.gen_manifest_url(), "uid": digit.get_ref()}
        for digit in digits
    ]


def regions_request(witnesses, treatment_id):
    """
    To relaunch extraction request in case the automatic process has failed
    """
    tasking.task_request(
        "regions",
        witnesses,
        treatment_id,
    )


def check_regions_txt_file(file_content):
    """
    Check that the TXT of the file content really contains annotations
    Should look something like this:
        1 img_0001.jpg
        x y h w
        x y h w
        2 img_0002.jpg
        x y h w

    :param file_content:
    :return:
    """
    # Either contains a number then an img.jpg / Or a series of 4 numbers
    pattern = re.compile(r"^\d+\s+\S+\.jpg$|^\d+\s\d+\s\d+\s\d+$")
    for line in file_content.split("\n"):
        if line == "":
            continue
        if not pattern.match(line):
            log(f"[check_regions_txt_file] incorrect line {line}")
            return False
    return True


def check_regions_json_file(file_content):
    """
    Check that the JSON of the file content really contains annotations
    Should contain something like this:
        [{
            "source": "image_name.jpg",
            "width": 1912,
            "height": 2500,
            "crops": [
              {
                "bbox": "gb638390",
                "crop_id": "image_name.jpg-gb638390",
                "source": "image_name.jpg",
                "confidence": 0.8001,
                "absolute": {
                  "x1": 866, "y1": 422, "x2": 1295, "y2": 1048, "width": 429, "height": 626
                },
                "relative": {
                  "x1": 0.4529, "y1": 0.1688, "x2": 0.6773, "y2": 0.4192, "width": 0.2244, "height": 0.2504
                }
              },
              {...}
            ],
            "doc_uid": "doc_ref"
          },{...}]
    :param file_content:
    :return:
    """
    try:
        if not isinstance(file_content, list):
            return False

        for annotation in file_content:
            if not all(key in annotation for key in ["source", "crops"]):
                return False

            if not isinstance(annotation["crops"], list):
                return False

            for crop in annotation["crops"]:
                if not all(key in crop for key in ["source", "absolute"]):
                    return False

                # for coords in crop['absolute']:
                #     if not all(key in coords for key in ['x1', 'y1', 'width', 'height']):
                #         return False
        return True
    except Exception as e:
        log(f"[check_regions_json_file] incorrect data", e)
        return False
