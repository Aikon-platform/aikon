import json

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

"""
VIEWS THAT SERVE AS ENDPOINTS
ONLY FOR API CALLS
"""


@csrf_exempt
def save_document_set(request):
    """
    Endpoint used to create/update a document set
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))

            witness_ids = data.get("witness_ids", [])
            series_ids = data.get("series_ids", [])
            regions_ids = data.get("regions_ids", [])

            # TODO create logic for saving document set etc.

            if len(witness_ids) + len(series_ids) + len(regions_ids) == 0:
                return JsonResponse(
                    {"error": "No documents to save in the set"}, status=400
                )
            return JsonResponse({"message": "Document set saved successfully"})
        except Exception as e:
            return JsonResponse({"message": "Error saving score files"}, status=500)
    return JsonResponse({"message": "Invalid request"}, status=400)
