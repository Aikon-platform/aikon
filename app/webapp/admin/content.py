import nested_admin
from django.contrib import admin

from app.webapp.admin.role import RoleInline
from app.webapp.admin.admin import UnregisteredAdmin
from app.webapp.models.content import Content, get_name


@admin.register(Content)
class ContentAdmin(UnregisteredAdmin):
    # NOTE useful class for list and search features
    search_fields = ("work", "witness")
    fields = [
        "work",
        ("page_min", "page_max"),
        ("date_min", "date_max"),
        ("place", "lang"),
    ]
    inlines = [RoleInline]


class ContentInline(nested_admin.NestedStackedInline):
    model = Content
    extra = 1  # Display only one empty form in the parent form

    fields = [
        "work",
        ("page_min", "page_max"),
        ("date_min", "date_max"),
        ("place", "lang"),
    ]

    autocomplete_fields = ("work", "place")
    inlines = [RoleInline]


class ContentWorkInline(nested_admin.NestedStackedInline):
    model = Content
    verbose_name_plural = ""
    extra = 0  # 1
    fields = ["work"]  # ("page_min", "page_max")
    autocomplete_fields = ("work",)

    # def has_add_permission(self, request, obj=None):
    #     # Returning False will hide the "Add another" link
    #     return False


# TabularInline: most common type of inline model. It displays the related models in a tabular format, similar to a table. Each row represents a related model instance. It is suitable for models with a large number of instances and provides a compact view.
# StackedInline: inline model displays the related models as a stack of collapsible fieldsets. Each fieldset represents a related model instance. It provides a more visually prominent display of related models compared to TabularInline but takes up more vertical space.
# InlineModelAdmin: generic inline model that provides more customization options. It allows you to define the layout and rendering of the inline form fields using the fields, fieldsets, or form attributes. It provides more flexibility but requires more manual configuration.
# GenericTabularInline and GenericStackedInline: inline models are used when working with generic relations in Django, which allow a model to have a foreign key relationship with any model. GenericTabularInline and GenericStackedInline provide the tabular and stacked representations, respectively, for the related generic models.
