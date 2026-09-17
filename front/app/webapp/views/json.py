from django.http import JsonResponse

from app.webapp.tasks import generate_all_json, regenerate_witness_json
from webapp.utils.logger import log


def json_regeneration(request):
    task = generate_all_json.delay()
    return JsonResponse(
        {"message": "JSON regeneration task started", "task_id": str(task.id)}
    )


def witness_json_regeneration(request, wid):
    try:
        task = regenerate_witness_json.delay(wid)
    except Exception as e:
        log(f"[witness_json_regeneration] failed for #{wid}", e)
        return JsonResponse({"error": str(e)})
    return JsonResponse(
        {"message": "Witness JSON regeneration task started", "task_id": str(task.id)}
    )
