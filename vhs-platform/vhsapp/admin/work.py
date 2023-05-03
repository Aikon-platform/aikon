from django.contrib import admin
from admin_searchable_dropdown.filters import AutocompleteFilter

from vhsapp.models.work import Work, get_name


class WorkFilter(AutocompleteFilter):
    title = get_name("Work")
    field_name = "work"  # name of field in Content
