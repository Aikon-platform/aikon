import json
from pathlib import Path

from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from app.webapp.models.digitization import Digitization
from app.webapp.models.document_set import DocumentSet
from app.webapp.models.region_extraction import RegionExtraction
from app.webapp.models.witness import Witness

from app.webapp.utils.logger import log
from app.webapp.utils.paths import MEDIA_PATH
from app.webapp.utils.region_extraction import create_empty_region_extraction
from app.webapp.utils.paths import MEDIA_PATH, REGIONS_PATH
from app.webapp.utils.region_extraction import create_empty_region_extraction
from app.webapp.utils.functions import page_bounds
from app.webapp.utils.tasking import create_doc_set
from app.webapp.utils.constants import PAGE_LEN
from app.webapp.utils.iiif.annotation import get_record_annotations

from app.webapp.tasks import generate_all_json

# TODO ORGANISE THESE VIEWS BETTER


def json_regeneration(request):
    task = generate_all_json.delay()
    return JsonResponse(
        {"message": "JSON regeneration task started", "task_id": str(task.id)}
    )


def get_document_set_info(request, dsid=None):
    if dsid is None:
        return JsonResponse({"error": "No document set id provided"}, status=400)

    try:
        ds = DocumentSet.objects.get(id=dsid)
    except DocumentSet.DoesNotExist:
        return JsonResponse(
            {"error": f"Document set #{dsid} does not exist"}, status=404
        )

    witnesses = ds.all_witnesses()
    result = {"Witness": {}, "Series": {}, "Digitization": {}}

    def update_date_range(target, min_date, max_date):
        if min_date is not None:
            if target["min_date"] is None or min_date < target["min_date"]:
                target["min_date"] = min_date
        if max_date is not None:
            if target["max_date"] is None or max_date > target["max_date"]:
                target["max_date"] = max_date

    def string_to_color(s: str) -> str:
        import hashlib

        index = int(hashlib.md5(str(s).encode()).hexdigest(), 16) % 1000
        golden_angle = 137.5
        saturations = [85, 70, 60]
        lightnesses = [50, 65, 40]
        hue = int((index * golden_angle) % 360)
        saturation = saturations[index % len(saturations)]
        lightness = lightnesses[(index // len(saturations)) % len(lightnesses)]
        return f"hsl({hue}, {saturation}%, {lightness}%)"

    for witness in witnesses:
        digits = witness.get_digits()
        series = witness.series
        wit_title = witness.__str__()
        min_date, max_date = witness.get_dates()
        digit_ids = [d.id for d in digits]
        series_id = series.id if series is not None else None

        result["Witness"][witness.id] = {
            # **(witness.json or {}),
            "id": witness.id,
            "color": string_to_color(f"wit{witness.id}"),
            "title": wit_title,
            "min_date": min_date,
            "max_date": max_date,
            "digitization_id": digit_ids,
            "series_id": series_id,
        }

        for digit in digits:
            metadata = digit.json or {}
            result["Digitization"][digit.id] = {
                "id": digit.id,
                "color": string_to_color(f"digit{digit.id}"),
                "title": f"{wit_title} ({digit.get_digit_type()} #{digit.id})",
                "witness_id": witness.id,
                "series_id": series_id,
                "min_date": min_date,
                "max_date": max_date,
                # additional data needed
                "zeros": metadata.get("zeros", 4),
                "img_nb": metadata.get("img_nb", 0),
                "url": metadata.get("url", digit.get_manifest_url()),
                "ref": metadata.get("ref", digit.get_ref()),
            }

        if not series:
            continue

        if series.id not in result["Series"]:
            result["Series"][series_id] = {
                # **(series.json or {}),
                "id": series_id,
                "color": string_to_color(f"ser{series_id}"),
                "title": series.__str__(),
                "min_date": min_date,
                "max_date": max_date,
                "witness_ids": [witness.id],
                "digitization_ids": digit_ids,
            }
        else:
            entry = result["Series"][series_id]
            update_date_range(entry, min_date, max_date)
            entry["witness_ids"].append(witness.id)
            entry["digitization_ids"].extend(
                d for d in digit_ids if d not in entry["Digitization"]
            )

    # Sort each entity group by min_date (None last)
    def sort_key(item):
        d = item[1]["min_date"]
        return (d is None, d or 0)

    for key in result:
        result[key] = dict(sorted(result[key].items(), key=sort_key))

    return JsonResponse(result)


def save_document_set(request, dsid=None):
    """
    Endpoint used to create/update a document set
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))

            selection = data.get("selection", [])
            set_name = data.get("title", None)
            witness_ids = data.get("Witness", [])
            series_ids = data.get("Series", [])
            work_ids = data.get("Work", [])
            shared_with = data.get("User", [])
            is_public = data.get("is_public", False)

            if len(witness_ids) + len(series_ids) + len(work_ids) == 0:
                return JsonResponse(
                    {"error": "No documents to save in the set"}, status=400
                )

            try:
                keep_title = False
                if dsid:
                    ds = DocumentSet.objects.get(id=dsid)
                    ds.wit_ids = witness_ids
                    ds.ser_ids = series_ids
                    ds.work_ids = work_ids
                    ds.shared_with = shared_with
                    ds.is_public = is_public
                else:
                    ds, is_new = create_doc_set(
                        {
                            "wit_ids": witness_ids,
                            "ser_ids": series_ids,
                            "work_ids": work_ids,
                        },
                        user=request.user,
                        shared_with=shared_with,
                        is_public=is_public,
                    )
                    keep_title = not is_new

                ds.selection = selection
                title = ds.title if keep_title else set_name
                ds.title = f"{title} #{ds.id}" if "#" not in title else title

                ds.save()

            except Exception as e:
                return JsonResponse(
                    {"error": f"Failed to save document set: {e}"}, status=500
                )
            return JsonResponse(
                {
                    "message": "Document set saved successfully",
                    "document_set_id": ds.id,
                    "document_set_title": ds.title,
                }
            )
        except Exception as e:
            return JsonResponse(
                {"message": f"Error saving score files: {e}"}, status=500
            )
    return JsonResponse({"message": "Invalid request"}, status=400)
