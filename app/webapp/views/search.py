from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.core.paginator import Paginator
from django_filters import FilterSet

from app.webapp.search_filters import WitnessFilter
from app.webapp.models.witness import Witness


def search_records(request, record_filter: FilterSet):
    paginator = Paginator(record_filter.qs, 25)
    page_number = request.GET.get("p", 1)
    page_obj = paginator.get_page(page_number)

    results = [obj.to_json() for obj in page_obj]

    return {
        "results": results,
        "count": record_filter.qs.count(),
        # "num_pages": paginator.num_pages,
        "current_page": page_obj.number,
    }


@require_GET
def search_witnesses(request):
    witness_list = Witness.objects.order_by("id")
    witness_filter = WitnessFilter(request.GET, queryset=witness_list)

    return JsonResponse(search_records(request, witness_filter))
