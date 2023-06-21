from admin_searchable_dropdown.filters import AutocompleteFilter
from django.contrib import admin, messages

from app.webapp.models.OLD.models import (
    DigitizedVersion,
    Author,
    Work,
)

from app.webapp.utils.constants import (
    SITE_HEADER,
    SITE_TITLE,
    SITE_INDEX_TITLE,
    TRUNCATEWORDS,
    MAX_ITEMS,
    MANIFEST_AUTO,
    MANIFEST_V2,
)


"""
Admin site
"""
admin.site.site_header = SITE_HEADER
admin.site.site_title = SITE_TITLE
admin.site.index_title = SITE_INDEX_TITLE


class AuthorFilter(AutocompleteFilter):
    title = "Auteur"  # Display title
    field_name = "author"  # Name of the foreign key field


class WorkFilter(AutocompleteFilter):
    title = "Titre de l'oeuvre"
    field_name = "work"


class DescriptiveElementsFilter(admin.SimpleListFilter):
    # Filter options in the right sidebar
    title = "Catégorie"
    # Parameter for the filter that will be used in the URL query
    parameter_name = "category"

    def lookups(self, request, model_admin):
        return (
            ("hn", "Histoire naturelle"),
            ("sm", "Sciences mathématiques"),
        )

    def queryset(self, request, queryset):
        if self.value() == "hn":
            return queryset.filter(
                descriptive_elements__contains="Histoire naturelle",
            )
        if self.value() == "sm":
            return queryset.filter(
                descriptive_elements__contains="Sciences mathématiques",
            )


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_filter = ("name",)
    list_per_page = 5

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index
        """
        return {}


@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    search_fields = ("title",)
    list_filter = ("title",)
    list_per_page = 5

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index
        """
        return {}


@admin.register(DigitizedVersion)
class DigitizedVersionAdmin(admin.ModelAdmin):
    search_fields = ("source",)
    list_filter = ("source",)
    list_per_page = 5

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index
        """
        return {}
