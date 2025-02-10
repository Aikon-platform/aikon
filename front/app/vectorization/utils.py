import os
import shutil
from pathlib import Path
from zipfile import ZipFile
from stream_unzip import stream_unzip
import requests

from app.config.settings import APP_URL, APP_NAME
from app.vectorization.const import VECTO_MODEL_EPOCH, SVG_PATH
from app.webapp.models.digitization import Digitization
from app.webapp.models.regions import Regions
from app.webapp.models.witness import Witness
from app.webapp.utils import tasking

from app.webapp.utils.logger import log


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
        "vectorization",
        {"model": f"{VECTO_MODEL_EPOCH}"},
    )


def process_results(data, completed=True):
    """
    :param data["output"]: {
        doc_id,: result_url,
        ?[doc_id: result_url,]
        ?["error": [list of error message]]
    }
    :param completed: whether the treatment is achieved or these are intermediary results
    :return:
    """
    output = data.get("output", None)
    if not data or not output:
        raise ValueError("No SVG results to unzip")

    if not os.path.exists(SVG_PATH):
        os.makedirs(SVG_PATH)

    for doc_id, result_url in output.items():
        if doc_id == "error":
            log(result_url)
            continue

        result_dir = SVG_PATH / doc_id

        if result_dir.exists() and any(result_dir.glob("*.svg")):
            # if the path already exists and contains svg file,
            # means that it was already downloaded
            continue

        try:
            res = requests.get(result_url, stream=True)
            res.raise_for_status()

            result_dir.mkdir(parents=True, exist_ok=True)
            zip_result_file = result_dir / "results.zip"

            with open(zip_result_file, "wb") as f:
                for chunk in res.iter_content(chunk_size=8192):
                    f.write(chunk)

            with (ZipFile(zip_result_file, "r") as zip_ref):
                for file_info in zip_ref.infolist():
                    filename = file_info.filename
                    if not filename.endswith(".svg"):
                        continue

                    file_path = result_dir / os.path.basename(filename)
                    with zip_ref.open(file_info) as input, open(
                        file_path, "wb"
                    ) as output:
                        output.write(input.read())

        except requests.exceptions.HTTPError as e:
            log(f"[save_svg_files] Error extracting SVG files from {doc_id}", e)
            continue

        return True


def prepare_document(document: Witness | Digitization | Regions, **kwargs):
    if document.is_vectorized():
        return []

    regions = document.get_regions() if hasattr(document, "get_regions") else [document]

    return [
        {"type": "url_list", "src": f"{APP_URL}/{APP_NAME}/{ref}/list", "uid": ref}
        for ref in [region.get_ref() for region in regions]
    ]


def vectorization_request_for_one(regions):
    """
    To relaunch vectorization request for one witness in case the automatic process has failed
    """
    tasking.task_request("vectorization", regions)


def delete_and_relaunch_request(regions):
    """
    Request to the API endpoint to delete imgs from the repo corresponding to doc_id + relaunch the vectorization
    """
    tasking.task_request("vectorization", regions, None, endpoint="delete_and_relaunch")


def reset_vectorization(regions: Regions):
    try:
        svg_dir = os.path.join(SVG_PATH, regions.get_ref())
        if os.path.exists(svg_dir):
            shutil.rmtree(svg_dir)
            # TODO send request to delete SVG to API
            return True
        log(f"[reset_vectorization] Folder {svg_dir} does not exist")
    except Exception as e:
        log(
            f"[reset_vectorization] Error removing SVG folder for Regions #{regions.id}",
            e,
        )
        return False
    return False
