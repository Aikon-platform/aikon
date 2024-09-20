from django.db.models import Q, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.core.paginator import Paginator
from django.db import models

from app.webapp.models.document_set import DocumentSet
from app.webapp.models.series import Series
from app.webapp.models.treatment import Treatment
from app.webapp.models.work import Work
from app.webapp.search_filters import (
    WitnessFilter,
    TreatmentFilter,
    WorkFilter,
    SeriesFilter,
    DocumentSetFilter,
)
from app.webapp.models.witness import Witness
from app.webapp.utils.constants import PAGE_LEN


def paginated_records(request, records):
    paginator = Paginator(records, PAGE_LEN)
    page_number = request.GET.get("p", 1)
    page_obj = paginator.get_page(page_number)

    results = [json_obj for obj in page_obj if (json_obj := obj.json) is not None]

    return {
        "results": results,
        "count": records.count() if hasattr(records, "count") else len(records),
        # "num_pages": paginator.num_pages,
        "current_page": page_obj.number,
    }


@require_GET
def search_witnesses(request):
    witness_filter = WitnessFilter(request.GET, queryset=Witness.objects.order_by("id"))
    return JsonResponse(paginated_records(request, witness_filter.qs))


@require_GET
def search_treatments(request):
    user = request.user
    treatment_list = Treatment.objects.all().order_by("-requested_on")
    if not user.is_superuser:
        treatment_list = treatment_list.filter(requested_by=user)

    treatment_filter = TreatmentFilter(request.GET, queryset=treatment_list)
    return JsonResponse(paginated_records(request, treatment_filter.qs))


@require_GET
def search_works(request):
    work_filter = WorkFilter(request.GET, queryset=Work.objects.order_by("id"))
    return JsonResponse(paginated_records(request, work_filter.qs))


@require_GET
def search_series(request):
    series_filter = SeriesFilter(request.GET, queryset=Series.objects.order_by("id"))
    return JsonResponse(paginated_records(request, series_filter.qs))


class ArrayLength(models.Func):
    function = "CARDINALITY"


@require_GET
def search_document_set(request):
    user = request.user

    wit_len = Coalesce(ArrayLength("wit_ids"), Value(0))
    ser_len = Coalesce(ArrayLength("ser_ids"), Value(0))
    work_len = Coalesce(ArrayLength("work_ids"), Value(0))

    base_queryset = DocumentSet.objects.annotate(set_len=wit_len + ser_len + work_len)

    if user.is_superuser:
        queryset = base_queryset.filter(set_len__gt=1)
    else:
        queryset = base_queryset.filter(
            Q(is_public=True) | Q(user=user) | Q(set_len__gt=1)
        )

    doc_sets = DocumentSetFilter(request.GET, queryset=queryset.order_by("-id"))

    return JsonResponse(paginated_records(request, doc_sets.qs))
