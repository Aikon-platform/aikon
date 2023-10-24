import nested_admin
from django.contrib import admin

from app.webapp.admin import RoleInline
from app.webapp.admin.witness import WitnessInline
from app.webapp.models.series import Series
from app.webapp.models.edition import get_name
from app.webapp.models.witness import Witness
from app.webapp.utils.functions import format_start_end


@admin.register(Series)
class SeriesAdmin(nested_admin.NestedModelAdmin):
    ordering = ("id",)
    list_per_page = 100
    search_fields = ("edition_name",)
    # TODO: "manifest_link", "is_annotated"
    list_display = (
        "id",
        "edition",
        "get_works",
        "get_authors",
        "get_publisher",
        "get_place",
        "get_date",
        "is_public",
    )
    list_display_links = ("edition",)

    class Meta:
        verbose_name = get_name("Series")
        verbose_name_plural = get_name("Series", True)

    class Media:
        css = {"all": ("css/form.css", "css/series-form.css")}
        js = ("js/witness-form.js",)

    fields = ["edition", ("date_min", "date_max"), "notes", "is_public"]

    inlines = [RoleInline, WitnessInline]

    @admin.display(description=get_name("Work"))
    def get_works(self, obj):
        return obj.get_work_titles()

    @admin.display(
        description=get_name("Person", plural=True),
        # ordering= TODO find something to order the column
    )
    def get_authors(self, obj: Witness):
        return obj.get_person_names()

    @admin.display(description=get_name("publisher"))
    def get_publisher(self, obj):
        return obj.edition.publisher

    @admin.display(description=get_name("pub_place"))
    def get_place(self, obj):
        return obj.edition.place

    @admin.display(description="Date")
    def get_date(self, obj):
        return format_start_end(obj.date_min, obj.date_max)

    # NOTE: attribute to use to change to template of witness (template at: templates/admin/series_form.html)
    # change_form_template = "admin/series_form.html"
