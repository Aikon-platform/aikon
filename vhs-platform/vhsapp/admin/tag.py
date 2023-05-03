from django.contrib import admin

from vhsapp.models.tag import Tag, get_name


class TagFilter(admin.SimpleListFilter):
    # Filter options in the right sidebar
    title = get_name("Tag")
    # Parameter for the filter that will be used in the URL query
    parameter_name = "tag"

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
