import json

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import CreateView, DetailView, View, ListView, UpdateView
from django.shortcuts import get_object_or_404
from django.urls import reverse

from app.webapp.models.series import Series
from app.webapp.models.work import Work
from app.webapp.search_filters import (
    WitnessFilter,
    TreatmentFilter,
    WorkFilter,
    SeriesFilter,
)
from app.webapp.forms import *
from app.webapp.forms.treatment import TreatmentForm
from app.webapp.models.regions import Regions
from app.webapp.models.treatment import Treatment
from app.webapp.models.witness import Witness
from app.webapp.utils.constants import MANIFEST_V2


class AbstractView(LoginRequiredMixin, View):
    model = None
    template_name = None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["view_title"] = self.get_view_title()
        context["model_name"] = str(
            getattr(self, "model_name", self.model._meta.model_name)
        ).lower()
        context["model_title"] = str(
            getattr(self, "model_title", self.model._meta.verbose_name)
        )
        context["app_name"] = "webapp"
        context["user"] = (
            self.request.user if self.request.user.is_authenticated else None
        )
        return context

    def get_view_title(self):
        return "Placeholder title"


class AbstractRecordView(AbstractView, CreateView):
    template_name = "webapp/view.html"
    pk_url_kwarg = "id"

    def get_view_title(self):
        return f"View {self.model._meta.verbose_name}"

    def get_success_url(self):
        return reverse(f"{self.model._meta.name}_list")

    def get_record(self):
        return get_object_or_404(self.model, pk=self.kwargs.get(self.pk_url_kwarg))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if "id" in self.kwargs:
            kwargs["instance"] = self.get_record()
        return kwargs


class AbstractRecordCreate(AbstractRecordView, CreateView):
    template_name = "webapp/form.html"

    def get_view_title(self):
        return f"Add {self.model._meta.verbose_name}"

    def get_success_url(self):
        return reverse(f"{self.model._meta.name}_list")


class AbstractRecordUpdate(AbstractRecordView, UpdateView):
    template_name = "webapp/form.html"

    def get_view_title(self):
        return f"Change {self.model._meta.verbose_name}"


class AbstractRecordList(AbstractView, ListView):
    template_name = "webapp/list.html"
    paginate_by = 50
    ordering = ["id"]

    # def get_ordering(self):
    #     ordering = self.request.GET.get('ordering', '-date_created')
    #     return ordering

    def get_view_title(self):
        # TODO find better name (bilingual)
        return f"List of {self.model._meta.verbose_name_plural}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_fields"] = []

        return context


class WitnessView(AbstractRecordView):
    model = Witness
    form_class = WitnessForm


class WitnessCreate(AbstractRecordCreate):
    model = Witness
    form_class = WitnessForm


class WitnessUpdate(AbstractRecordUpdate):
    model = Witness
    form_class = WitnessForm


class WitnessList(AbstractRecordList):
    model = Witness

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_fields"] = WitnessFilter().to_form_fields()

        return context


class WitnessRegionsView(AbstractRecordView):
    # f"witness/<int:wid>/regions/"
    # display only all Regions objects for a given Witness
    model = Witness
    template_name = "webapp/regions.html"
    pk_url_kwarg = "id"
    fields = []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["regions_ids"] = []
        context["is_validated"] = True
        context["img_nb"] = None

        witness = self.get_record()
        context["witness"] = witness.to_json()
        if len(witness.get_digits()) == 0:
            # TODO handle case where no digitization is available
            pass

        for regions in witness.get_regions():
            context["regions_ids"].append(regions.id)
            # TODO handle multiple manifest for multiple regions
            context["manifest"] = regions.gen_manifest_url(version=MANIFEST_V2)
            context["img_prefix"] = regions.get_ref().split("_anno")[0]
            if context["img_nb"] is None:
                context["img_nb"] = regions.img_nb()
            if not regions.is_validated:
                context["is_validated"] = False

        return context


class RegionsView(AbstractRecordView):
    # f"witness/<int:wid>/regions/<int:rid>/"
    # display only one Regions object
    model = Regions
    template_name = "webapp/regions.html"
    fields = []
    pk_url_kwarg = "rid"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["witness_id"] = self.kwargs["wid"]
        context["regions_id"] = self.kwargs["rid"]

        regions = self.get_record()
        context["witness"] = regions.get_witness().to_json()
        context["is_validated"] = regions.is_validated
        context["manifest"] = regions.gen_manifest_url(version=MANIFEST_V2)
        context["img_prefix"] = regions.get_ref().split("_anno")[0]
        context["img_nb"] = regions.img_nb()
        return context


class TreatmentCreate(AbstractRecordCreate):
    model = Treatment
    form_class = TreatmentForm

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.requested_by = self.request.user
        self.object = form.save()

        return super().form_valid(form)

    def get_success_url(self):
        # Return the URL for the TreatmentList view
        return reverse("webapp:treatment_list")


class TreatmentList(AbstractRecordList):
    model = Treatment

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_fields"] = TreatmentFilter().to_form_fields()

        return context


class WorkList(AbstractRecordList):
    model = Work

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_fields"] = WorkFilter().to_form_fields()

        return context


class SeriesList(AbstractRecordList):
    model = Series

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_fields"] = SeriesFilter().to_form_fields()

        return context


# TODO DocumentSetList, RegionsSetList
