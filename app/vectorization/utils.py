import os
import shutil
import zipfile

from app.config.settings import APP_URL, APP_NAME
from app.vectorization.const import VECTO_MODEL_EPOCH, SVG_PATH
from app.webapp.models.digitization import Digitization
from app.webapp.models.regions import Regions
from app.webapp.models.witness import Witness
from app.webapp.utils import tasking

from app.webapp.utils.logger import log


def prepare_document(document: Witness | Digitization | Regions, **kwargs):
    if document.is_vectorized():
        return []

    regions = document.get_regions() if hasattr(document, "get_regions") else [document]

    return [
        {"type": "url_list", "src": f"{APP_URL}/{APP_NAME}/{ref}/list"}
        for ref in [region.get_ref() for region in regions]
    ]


def prepare_request(witnesses, treatment_id):
    tasking.prepare_request(
        witnesses,
        treatment_id,
        prepare_document,
        "vectorization",
        {"model": f"{VECTO_MODEL_EPOCH}"},
    )


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


def save_svg_files(zip_file):
    """
    Extracts SVG files from a ZIP file and saves them to a folder named after regions.ref inside SVG_PATH,
    named after the ZIP file (without extension).
    """
    if not os.path.exists(SVG_PATH):
        os.makedirs(SVG_PATH)

    # Create a subdirectory named after the ZIP file
    zip_name = os.path.splitext(os.path.basename(zip_file))[0]
    subdir = os.path.join(SVG_PATH, zip_name)
    os.makedirs(subdir, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_file, "r") as zip_ref:
            for file_info in zip_ref.infolist():
                if file_info.filename.endswith(".svg"):
                    file_path = os.path.join(
                        subdir, os.path.basename(file_info.filename)
                    )
                    with zip_ref.open(file_info) as svg_file, open(
                        file_path, "wb"
                    ) as output_file:
                        output_file.write(svg_file.read())

    except Exception as e:
        log(f"[save_svg_files] Error extracting SVG files from {zip_file}", e)
        return False
    return True


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
