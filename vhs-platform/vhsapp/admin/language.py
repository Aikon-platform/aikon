from admin_searchable_dropdown.filters import AutocompleteFilter

from vhsapp.models.language import get_name


class LanguageFilter(AutocompleteFilter):
    title = get_name("Language")
    field_name = get_name("lang")  # name of field in Content model


# NOTE: no form because all languages are added with populate_language migration
