import nested_admin
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse

from app.config.settings import APP_LANG
from app.webapp.admin.role import RoleInline
from app.webapp.admin.witness import WitnessInline
from app.webapp.models.series import Series, get_name
from app.webapp.models.edition import get_name as ed_get_name
from app.webapp.models.utils.constants import TPR, TPR_ABBR
from app.webapp.utils.constants import TRUNCATEWORDS
from app.webapp.utils.functions import format_start_end, format_dates, truncate_words


@admin.register(Series)
class SeriesAdmin(nested_admin.NestedModelAdmin):
    ordering = ("id",)
    list_per_page = 100
    search_fields = ("edition__name",)
    list_display = (
        "id",
        "get_edition",  # "edition",
        "get_works",
        "get_roles",
        "get_publisher",
        "get_place",
        "get_date",
        "is_public",
    )
    list_display_links = ("get_edition",)  # ("edition",)

    # banner = (
    #     f"{get_name('Series')} identification"
    #     if APP_LANG == "en"
    #     else f"Identification de la {get_name('Series')}"
    # )

    class Meta:
        verbose_name = get_name("Series")
        verbose_name_plural = get_name("Series", True)

    class Media:
        css = {"all": ("css/series-form.css",)}
        js = ("js/series-form.js",)

    # NOTE: attribute to use to change to template of witness (template at: templates/admin/form.html)
    change_form_template = "admin/form.html"

    fields = [
        ("work", "edition"),
        ("date_min", "date_max"),
        "place",
        "notes",
        "tags",
        "is_public",
    ]
    inlines = [RoleInline, WitnessInline]
    autocomplete_fields = ("work", "edition", "place")

    @admin.display(description=get_name("Edition"))
    def get_edition(self, obj):
        return truncate_words(obj.edition.__str__(), TRUNCATEWORDS)

    @admin.display(description=get_name("Work"))
    def get_works(self, obj):
        return obj.get_work_titles()

    @admin.display(
        description=get_name("Person", plural=True),
        # ordering= TODO find something to order the column
    )
    def get_roles(self, obj: Series):
        return obj.get_person_names()

    @admin.display(description=ed_get_name("publisher"))
    def get_publisher(self, obj):
        return obj.edition.publisher

    @admin.display(description=ed_get_name("pub_place"))
    def get_place(self, obj):
        return obj.edition.place

    @admin.display(description="Date")
    def get_date(self, obj):
        return format_dates(obj.date_min, obj.date_max)

    def save_related(self, request, form, formset, change):
        super(SeriesAdmin, self).save_related(request, form, formset, change)

        for witness in form.instance.witness_set.all():
            if not witness.type:
                witness.type = TPR_ABBR
            if not witness.edition:
                witness.set_edition(form.instance.edition)
            if not witness.id_nb:
                vol_nb = (
                    f"{get_name('vol_nb')}{witness.volume_nb}"
                    if witness.volume_nb
                    else get_name("no_vol_nb")
                )
                witness.set_id_nb(vol_nb)
            if not witness.place:
                witness.set_conservation_place(form.instance.place)
            if len(witness.get_contents()) == 0:
                witness.add_content(form.instance.work, True)
            if not witness.user:
                witness.user = request.user
            for content in witness.get_contents():
                if not content.date_min:
                    content.date_min = form.instance.date_min
                if not content.date_max:
                    content.date_max = form.instance.date_max
                if not content.tags.all():
                    # Get series tags and create content tags
                    series_tags = form.instance.tags.all()
                    for series_tag in series_tags:
                        content.tags.add(series_tag)
                content.save()
            witness.save()

    def save_model(self, request, obj, form, change):
        # called on submission of form
        if not obj.user:
            obj.user = request.user
        obj.save()

    def response_add(self, request, obj, post_url_continue=None):
        return HttpResponseRedirect(reverse("webapp:series_list"))

    def response_change(self, request, obj):
        return HttpResponseRedirect(reverse("webapp:series_list"))

    def response_delete(self, request, obj_display, obj_id):
        return HttpResponseRedirect(reverse("webapp:series_list"))
