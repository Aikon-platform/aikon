from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import CreateView, DetailView, View, ListView, UpdateView
from django.urls import reverse

from app.webapp.forms import *
from app.webapp.models.witness import Witness


class AbstractView(LoginRequiredMixin):
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


class AbstractRecordCreate(AbstractView, CreateView):
    template_name = "webapp/form.html"

    def get_view_title(self):
        return f"Add {self.model._meta.verbose_name}"

    def get_success_url(self):
        return reverse(f"{self.model._meta.name}_list")


class AbstractRecordUpdate(AbstractView, UpdateView):
    template_name = "webapp/form.html"
    pk_url_kwarg = "id"

    def get_view_title(self):
        return f"Change {self.model._meta.verbose_name}"

    def get_success_url(self):
        return reverse(f"{self.model._meta.name}_list")


class AbstractRecordList(AbstractView, ListView):
    template_name = "webapp/list.html"
    paginate_by = 50

    def get_view_title(self):
        return f"List of {self.model._meta.verbose_name}"


class WitnessView(AbstractRecordView):
    model = Witness


class WitnessCreate(AbstractRecordCreate):
    model = Witness
    form_class = WitnessForm


class WitnessUpdate(AbstractRecordUpdate):
    model = Witness
    form_class = WitnessForm


class WitnessList(AbstractRecordList):
    model = Witness
