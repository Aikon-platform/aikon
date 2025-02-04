from django.contrib import admin
from admin_searchable_dropdown.filters import AutocompleteFilter
from django.http import HttpResponseRedirect
from django.urls import reverse

from app.webapp.admin.admin import UnregisteredAdmin
from app.webapp.forms import LanguageForm
from app.webapp.models.work import Work, get_name


class WorkFilter(AutocompleteFilter):
    title = get_name("Work")
    field_name = "work"  # name of field in Content


@admin.register(Work)
class WorkAdmin(UnregisteredAdmin):
    form = LanguageForm
    change_form_template = "admin/form.html"
    search_fields = ("title", "author__name")
    list_filter = ("title",)
    fields = [
        "title",
        "author",
        ("date_min", "date_max"),
        "place",
        "notes",
        "lang",
        "tags",
    ]
    autocomplete_fields = ("author", "place")

    def response_add(self, request, obj, post_url_continue=None):
        return HttpResponseRedirect(reverse("webapp:work_list"))

    def response_change(self, request, obj):
        return HttpResponseRedirect(reverse("webapp:work_list"))

    def response_delete(self, request, obj_display, obj_id):
        return HttpResponseRedirect(reverse("webapp:work_list"))

    # # # # # # # # # # # #
    #     PERMISSIONS     #
    # # # # # # # # # # # #

    def has_change_permission(self, request, obj=None):
        return True

    def has_view_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request, obj=None):
        return True


# class WorkInline(nested_admin.NestedStackedInline):
#     fields = ["title", "author", ("date_min", "date_max")]
