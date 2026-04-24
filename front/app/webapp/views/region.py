import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from app.webapp.models.region import Region
from app.webapp.models.region_extraction import RegionExtraction


def save_region(request, rid=None, reid=None):
    """
    Endpoint used to create/update a region
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))

            region_extraction = RegionExtraction.objects.get(id=reid).first()
            notes = data.get("notes", None)
            tags = data.get("tags", [])

            try:
                if rid:
                    r = Region.objects.get(id=rid)
                    r.notes = notes
                    r.tags = tags
                else:
                    region = Region.objects.create(
                        region_extraction=region_extraction,
                        notes=notes,
                        tags=tags,
                    )
                    region.save()

                r.save()

            except Exception as e:
                return JsonResponse(
                    {"error": f"Failed to save region: {e}"}, status=500
                )

            return JsonResponse(
                {
                    "message": "Region saved successfully",
                    "region_id": r.id,
                }
            )
        except Exception as e:
            return JsonResponse({"message": f"Error saving region: {e}"}, status=500)
    return JsonResponse({"message": "Invalid request"}, status=400)
