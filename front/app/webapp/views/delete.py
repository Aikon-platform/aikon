from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from app.webapp.models.document_set import DocumentSet
from app.webapp.models.edition import Edition
from app.webapp.models.series import Series
from app.webapp.models.treatment import Treatment
from app.webapp.models.witness import Witness
from app.webapp.models.work import Work

#######################################
#            DELETE VIEWS             #
# endpoints to erase database records #
#######################################


def delete_record(rec_id, rec_class):
    """
    Delete record instance from the db
    """
    if not rec_id:
        return JsonResponse({"error": "Invalid record ID"}, status=400)
    try:
        rec = rec_class.objects.get(id=rec_id)
        rec.delete()

        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": f"{rec_class} #{rec_id} not found"}, e)


@csrf_exempt
def delete_treatment(request, rec_id):
    # TODO delete results files ?
    return delete_record(rec_id, Treatment)


@csrf_exempt
def delete_doc_set(request, rec_id):
    return delete_record(rec_id, DocumentSet)


@csrf_exempt
def delete_work(request, rec_id):
    return delete_record(rec_id, Work)


@csrf_exempt
def delete_witness(request, rec_id):
    return delete_record(rec_id, Witness)


@csrf_exempt
def delete_series(request, rec_id):
    return delete_record(rec_id, Series)


@csrf_exempt
def delete_edition(request, rec_id):
    return delete_record(rec_id, Edition)
