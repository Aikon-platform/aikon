from dal import autocomplete

from django.http import HttpResponse, JsonResponse
from app.webapp.models.document_set import DocumentSet
from app.webapp.models.series import Series
from app.webapp.models.work import Work
from app.config.settings import (
    GEONAMES_USER,
)
from app.webapp.models.edition import Edition
from app.webapp.models.language import Language
from app.webapp.models.witness import Witness
from app.webapp.utils.constants import MAX_ROWS
from app.webapp.utils.functions import get_json

##########################
#   AUTOCOMPLETE VIEWS   #
# used in form dropdowns #
##########################


class PlaceAutocomplete(autocomplete.Select2ListView):
    def get_list(self):
        name = self.forwarded.get("name")
        query = name if name else self.q
        data = get_json(
            f"http://api.geonames.org/searchJSON?q={query}&maxRows={MAX_ROWS}&username={GEONAMES_USER}"
        )

        suggestions = []
        try:
            for suggestion in data["geonames"]:
                suggestions.append(
                    f"{suggestion['name']} | {suggestion.get('countryCode', '')}"
                )

            return suggestions
        except Exception as e:
            log("[place_autocomplete] Error fetching Geonames data.", e)
            suggestions.append("Error fetching geographical data.")

            return suggestions


def retrieve_place_info(request):
    """
    Extract the relevant information (country, latitude, longitude) from the Geonames API response
    """
    name = request.GET.get("name")
    countryCode = request.GET.get("countryCode")
    if name:
        data = get_json(
            f"http://api.geonames.org/searchJSON?q={name}&country={countryCode}&maxRows={MAX_ROWS}&username={GEONAMES_USER}"
        )
        country = data["geonames"][0].get("countryName")
        latitude = data["geonames"][0].get("lat")
        longitude = data["geonames"][0].get("lng")

        return JsonResponse(
            {
                "country": country,
                "latitude": f"{float(latitude):.4f}",
                "longitude": f"{float(longitude):.4f}",
            }
        )

    return JsonResponse({"country": "", "latitude": "", "longitude": ""})


class LanguageAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Ensure the user is authenticated
        if not self.request.user.is_authenticated:
            return Language.objects.none()

        qs = Language.objects.all()

        if self.q:
            qs = qs.filter(lang__icontains=self.q)

        return qs


class EditionAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Ensure the user is authenticated
        if not self.request.user.is_authenticated:
            return Edition.objects.none()

        qs = Edition.objects.all()

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs


class DocumentSetAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return DocumentSet.objects.none()

        qs = DocumentSet.objects.all()
        qs = qs.filter(user=self.request.user).all()

        if self.q:
            if self.q.isdigit():
                qs = qs.filter(id=int(self.q))
            else:
                qs = qs.filter(title__icontains=self.q)

        return qs

    def get_result_label(self, result):
        return f"{result}"


class WitnessAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Witness.objects.all()

        if self.q:
            qs = qs.filter(id__icontains=self.q)

        return qs


class SeriesAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Series.objects.all()

        if self.q:
            qs = qs.filter(id__icontains=self.q)

        return qs


class WorkAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Work.objects.all()

        if self.q:
            qs = qs.filter(id__icontains=self.q)

        return qs
