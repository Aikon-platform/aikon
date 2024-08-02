import nested_admin
from django.contrib import admin
from django.utils.safestring import mark_safe

from app.config.settings import APP_NAME, WEBAPP_NAME, APP_LANG
from app.webapp.admin import UnregisteredAdmin
from app.webapp.models.digitization import Digitization, get_name
from app.webapp.models.utils.constants import IMG, IMG_MSG
from app.webapp.utils.functions import gen_thumbnail, cls
from app.webapp.utils.iiif import gen_iiif_url, IIIF_ICON
from app.webapp.utils.iiif.gen_html import gen_btn
from app.webapp.utils.logger import log


@admin.register(Digitization)
class DigitizationAdmin(UnregisteredAdmin):
    # Class for list display and search features
    change_form_template = "admin/form.html"
    search_fields = ("witness",)
    list_per_page = 100
    list_display = (
        "thumbnail",
        "witness",
        "get_nb_pages",
        # todo btn to open mirador + nb of regions + is validated or not
    )

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)

    def thumbnail(self, obj: Digitization):
        if obj.digit_type == IMG:
            return gen_thumbnail(
                gen_iiif_url(obj.image.name.split("/")[-1]), obj.image.url
            )
        # TODO for other types

    def get_nb_pages(self, obj: Digitization):
        return obj.witness.nb_pages if obj.witness else None


############################
#          INLINE          #
############################


class DigitizationInline(nested_admin.NestedStackedInline):
    model = Digitization
    template = "admin/includes/inline_fieldset.html"
    extra = 1  # Display only one empty form in the parent form
    max_num = 5
    readonly_fields = ("digit_preview", "view_digit", "view_regions")

    fields = ["digit_type", "pdf", "manifest", "images", ("is_open", "source")]
    autocomplete_fields = ("source",)

    def digit_url(self):
        return f"/{APP_NAME}-admin/{WEBAPP_NAME}/digitization"

    @admin.display(description=get_name("Digitization"))
    def digit_preview(self, obj: Digitization):
        # TODO check is used else delete
        return mark_safe(
            f'<a href="{self.digit_url()}/?q={obj.id}" target="_blank">{IIIF_ICON} {IMG_MSG}</a>'
        )

    @admin.display(description=get_name("view_digit"))
    def view_digit(self, obj: Digitization):
        if obj.id:
            if obj.has_images():
                return gen_btn(obj, "view")
            if obj.has_digit():
                # if the digitization is associated with a pdf/manifest/img but no images on the server
                return gen_btn(obj, "no_digit")
            # if not obj.has_regions():
            #     return gen_btn(Digitization.objects.filter(pk=obj.id).first(), "view")

            # digit_btn = []
            # for regions in obj.get_regions():
            #     digit_btn.append(gen_btn(regions, "auto-view"))
            # return mark_safe("<br>".join(digit_btn))

        return "-"

    @admin.display(description=get_name("view_regions"))
    def view_regions(self, obj: Digitization):
        if obj.id and obj.has_images() and obj.has_regions():
            regions_btn = []
            for regions in obj.get_regions():
                regions_btn.append(gen_btn(regions, "regions"))
            return mark_safe("<br>".join(regions_btn))
        return "-"

    def get_fields(self, request, obj: Digitization = None):
        fields = list(super(DigitizationInline, self).get_fields(request, obj))

        if obj and obj.has_images():
            fields.append("view_digit")
            if obj.has_regions():
                fields.append("view_regions")

        return fields
