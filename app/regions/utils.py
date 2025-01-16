from app.regions.const import EXTRACTOR_MODEL
from app.webapp.models.digitization import Digitization
from app.webapp.models.regions import Regions
from app.webapp.models.witness import Witness
from app.webapp.utils import tasking
from app.webapp.utils.iiif.annotation import has_annotation
from app.webapp.utils.logger import log

################################################################
# ⚠️   prepare_request() & process_results() are mandatory  ⚠️ #
# ⚠️ function used by Treatment to generate request payload ⚠️ #
# ⚠️    and save results files when sends back by the API   ⚠️ #
################################################################


def prepare_request(witnesses, treatment_id):
    tasking.prepare_request(
        witnesses,
        treatment_id,
        prepare_document,
        "regions",
        {"model": f"{EXTRACTOR_MODEL}"},
    )


def process_results(data):
    # TODO
    # self.status = "PROCESSING RESULTS"
    #         self.result_full_path.mkdir(parents=True, exist_ok=True)
    #
    #         if data is not None:
    #             output = data.get("output", {})
    #             if not output:
    #                 self.on_task_error({"error": "No output data"})
    #                 return
    #
    #             self.regions = output.get("annotations", {})
    #             with open(self.task_full_path / f"{self.dataset.id}.json", "w") as f:
    #                 json.dump(self.regions, f)
    #
    #             dataset_url = output.get("dataset_url")
    #             if dataset_url:
    #                 self.dataset.api_url = dataset_url
    #                 self.dataset.save()
    #
    #             result = self.dataset.apply_cropping(self.get_bounding_boxes())
    #             if "error" in result:
    #                 # self.terminate_task(status="ERROR", error=traceback.format_exc())
    #                 self.on_task_error(result)
    #                 return
    #         else:
    #             self.on_task_error({"error": "No output data"})
    #             return
    #
    #         return super().on_task_success(data)

    #     if request.method == "POST":
    #         try:
    #             regions_file = request.FILES["annotation_file"]
    #             # treatment_id = request.POST.get("experiment_id")
    #         except Exception as e:
    #             log("[receive_regions_notification] No regions file received for", e)
    #             return JsonResponse({"message": "No regions file"}, status=400)
    #
    #         try:
    #             model = request.POST.get("model", "Unknown model")
    #         except Exception as e:
    #             log("[receive_regions_notification] Unable to retrieve model param", e)
    #             model = "Unknown model"
    #         file_content = regions_file.read()
    #         file_content = file_content.decode("utf-8")
    #
    #         if check_regions_file(file_content):
    #             process_regions_file.delay(file_content, digit.id, model)
    #
    #             return JsonResponse({"response": "OK"}, status=200)
    #
    #         return JsonResponse({"message": "Could not process regions file"}, status=400)
    #     else:
    #         return JsonResponse({"message": "Invalid request"}, status=400)

    pass


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


def regions_request(witnesses, treatment_id):
    """
    To relaunch extraction request in case the automatic process has failed
    """
    tasking.task_request(
        "regions",
        witnesses,
        treatment_id,
    )
