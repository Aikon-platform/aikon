from django.contrib import admin

from app.webapp.admin.admin import UnregisteredAdmin
from app.webapp.models.content import Content, get_name


@admin.register(Content)
class ContentAdmin(UnregisteredAdmin):
    search_fields = ("work", "witness")


class ContentInline(admin.StackedInline):
    model = Content
    # TODO create the sub-form for Contents inside the Witness and Series forms

    autocomplete_fields = ("work", "place")


# TabularInline: most common type of inline model. It displays the related models in a tabular format, similar to a table. Each row represents a related model instance. It is suitable for models with a large number of instances and provides a compact view.
# StackedInline: inline model displays the related models as a stack of collapsible fieldsets. Each fieldset represents a related model instance. It provides a more visually prominent display of related models compared to TabularInline but takes up more vertical space.
# InlineModelAdmin: generic inline model that provides more customization options. It allows you to define the layout and rendering of the inline form fields using the fields, fieldsets, or form attributes. It provides more flexibility but requires more manual configuration.
# GenericTabularInline and GenericStackedInline: inline models are used when working with generic relations in Django, which allow a model to have a foreign key relationship with any model. GenericTabularInline and GenericStackedInline provide the tabular and stacked representations, respectively, for the related generic models.
