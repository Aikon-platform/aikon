from django.db.models import Q, Value, IntegerField
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.core.paginator import Paginator
from django.db import models
from django.contrib.auth.models import User

from app.webapp.search_filters import *
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
    current_user = request.user

    if current_user.is_superuser:
        witnesses = Witness.objects.order_by("id")
    else:
        witnesses = Witness.objects.filter(
            Q(user=current_user)
            | Q(is_public=True)
            | Q(user__groups__in=current_user.groups.all())
        ).distinct()

    witness_filter = WitnessFilter(request.GET, queryset=witnesses)
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


@require_GET
def search_digitizations(request):
    digitization_filter = DigitizationFilter(
        request.GET, queryset=Digitization.objects.order_by("id")
    )
    return JsonResponse(paginated_records(request, digitization_filter.qs))


@require_GET
def search_regions(request):
    regions_filter = RegionsFilter(request.GET, queryset=Regions.objects.order_by("id"))
    return JsonResponse(paginated_records(request, regions_filter.qs))


class ArrayLength(models.Func):
    function = "CARDINALITY"
    output_field = IntegerField()


@require_GET
def search_document_set(request):
    user = request.user

    wit_len = Coalesce(ArrayLength("wit_ids"), Value(0))
    ser_len = Coalesce(ArrayLength("ser_ids"), Value(0))
    work_len = Coalesce(ArrayLength("work_ids"), Value(0))

    base_queryset = (
        DocumentSet.objects.all()
        .annotate(set_len=wit_len + ser_len + work_len)
        .filter(set_len__gt=1)
    )

    if user.is_superuser:
        queryset = base_queryset
    else:
        queryset = base_queryset.filter(
            Q(shared_with__contains=[user.id]) | Q(user=user)
        ).distinct()

    doc_sets = DocumentSetFilter(request.GET, queryset=queryset.order_by("-id"))

    return JsonResponse(paginated_records(request, doc_sets.qs))


@require_GET
def search_user(request):
    q = request.GET.get("q", "")

    user_list = User.objects.filter(username__icontains=q).all()

    return JsonResponse(
        {"users": [{"id": user.id, "username": str(user)} for user in user_list]}
    )
