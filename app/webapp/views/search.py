from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.core.paginator import Paginator

from app.webapp.models.series import Series
from app.webapp.models.treatment import Treatment
from app.webapp.models.work import Work
from app.webapp.search_filters import (
    WitnessFilter,
    TreatmentFilter,
    WorkFilter,
    SeriesFilter,
)
from app.webapp.models.witness import Witness


def paginated_records(request, records):
    paginator = Paginator(records, 25)
    page_number = request.GET.get("p", 1)
    page_obj = paginator.get_page(page_number)

    results = [obj.to_json() for obj in page_obj]

    return {
        "results": results,
        "count": records.count() if hasattr(records, "count") else len(records),
        # "num_pages": paginator.num_pages,
        "current_page": page_obj.number,
    }


@require_GET
def search_witnesses(request):
    witness_list = Witness.objects.order_by("id")
    witness_filter = WitnessFilter(request.GET, queryset=witness_list)
    return JsonResponse(paginated_records(request, witness_filter.qs))


@require_GET
def search_treatments(request):
    treatment_list = Treatment.objects.order_by("id")
    treatment_filter = TreatmentFilter(request.GET, queryset=treatment_list)
    return JsonResponse(paginated_records(request, treatment_filter.qs))


@require_GET
def search_works(request):
    work_list = Work.objects.order_by("id")
    work_filter = WorkFilter(request.GET, queryset=work_list)
    return JsonResponse(paginated_records(request, work_filter.qs))


@require_GET
def search_series(request):
    series_list = Series.objects.order_by("id")
    series_filter = SeriesFilter(request.GET, queryset=series_list)
    return JsonResponse(paginated_records(request, series_filter.qs))
