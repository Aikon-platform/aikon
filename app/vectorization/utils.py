import os
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
    Extracts SVG files from a ZIP file and saves them to the SVG_PATH directory.
    """
    # Vérifie si le répertoire SVG_PATH existe, sinon le crée
    if not os.path.exists(SVG_PATH):
        os.makedirs(SVG_PATH)

    try:
        with zipfile.ZipFile(zip_file, "r") as zip_ref:
            for file_info in zip_ref.infolist():
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


def reset_vectorization(regions: Regions):
    regions_id = regions.id
    try:
        regions_ref = regions.get_ref()
    except Exception as e:
        log(
            f"[reset_vectorization] Failed to retrieve region ref for id {regions_id}",
            e,
        )
        return False

    for file in os.listdir(SVG_PATH):
        # TODO change here once SVG files will be stored in different folders
        if regions_ref in file:
            try:
                os.remove(os.path.join(SVG_PATH, file))
            except OSError as e:
                log(f"[reset_vectorization] Error removing {file}", e)

    # TODO send request to delete svg to API
    return True
