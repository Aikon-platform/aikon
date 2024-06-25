import json

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import CreateView, DetailView, View, ListView, UpdateView
from django.shortcuts import get_object_or_404
from django.urls import reverse

from app.webapp.forms import *
from app.webapp.models.regions import Regions
from app.webapp.models.witness import Witness
from app.webapp.utils.functions import DateTimeEncoder, flatten
from app.webapp.utils.iiif.annotation import get_regions_annotations


class AbstractView(LoginRequiredMixin, View):
    model = None
    template_name = None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["view_title"] = self.get_view_title()
        context["record_type"] = str(
            getattr(self, "record_type", self.model._meta.model_name)
        ).lower()
        context["record_name"] = str(
            getattr(self, "record_type", self.model._meta.verbose_name)
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
        return f"List of {self.model._meta.verbose_name}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["json_object_list"] = json.dumps(
            [obj.to_json() for obj in context["object_list"]], cls=DateTimeEncoder
        )

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


class WitnessRegionsView(AbstractRecordView):
    # f"witness/<int:wid>/regions/"
    # display only all Regions objects for a given Witness
    model = Witness
    template_name = "webapp/regions.html"
    pk_url_kwarg = "id"
    fields = []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        anno_regions = {}
        context["regions_ids"] = []
        for regions in self.get_record().get_regions():
            anno_regions = get_regions_annotations(
                regions, as_json=True, r_annos=anno_regions
            )
            context["regions_ids"].append(regions.id)
            # TODO handle multiple manifest for multiple regions
            context["manifest"] = regions.gen_manifest_url()
            context["img_prefix"] = regions.get_ref().split("_anno")

        context["regions_list"] = json.dumps(
            {k: v for canvases in anno_regions.values() for k, v in canvases.items()}
        )
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
        context["manifest"] = regions.gen_manifest_url()
        anno_regions = get_regions_annotations(regions, as_json=True)
        context["regions_list"] = json.dumps(
            {k: v for canvases in anno_regions.values() for k, v in canvases.items()}
        )
        context["img_prefix"] = regions.get_ref().split("_anno")
        return context
