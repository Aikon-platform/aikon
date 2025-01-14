from app.regions.const import EXTRACTOR_MODEL
from app.webapp.models.digitization import Digitization
from app.webapp.models.regions import Regions
from app.webapp.models.witness import Witness
from app.webapp.utils import tasking
from app.webapp.utils.iiif.annotation import has_annotation
from app.webapp.utils.logger import log


def prepare_document(document: Witness | Digitization | Regions, **kwargs):
    if type(document).__name__ == "Witness" and not document.has_digit():
        return []

    regions = document.get_regions() if hasattr(document, "get_regions") else [document]

    if any(
        region.model == kwargs["model"] and has_annotation(region.get_ref())
        for region in regions
    ):
        log(
            f"[prepare_document] Document #{document.get_ref()} already has regions extracted with {kwargs['model']}"
        )
        return []

    digits = document.get_digits() if hasattr(document, "get_digits") else [document]

    return [{"type": "iiif", "src": digit.gen_manifest_url()} for digit in digits]


def prepare_request(witnesses, treatment_id):
    tasking.prepare_request(
        witnesses,
        treatment_id,
        prepare_document,
        "regions",
        {"model": f"{EXTRACTOR_MODEL}"},
    )


def regions_request(witnesses, treatment_id):
    """
    To relaunch extraction request in case the automatic process has failed
    """
    tasking.task_request(
        "regions",
        witnesses,
        treatment_id,
    )
