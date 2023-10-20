import nested_admin
from django.contrib import admin
from django.utils.safestring import mark_safe

from app.config.settings import APP_NAME, WEBAPP_NAME, APP_LANG
from app.webapp.admin import UnregisteredAdmin
from app.webapp.models.digitization import Digitization, get_name
from app.webapp.models.utils.constants import IMG
from app.webapp.models.witness import Witness
from app.webapp.utils.functions import gen_thumbnail, cls
from app.webapp.utils.iiif import gen_iiif_url, IIIF_ICON
from app.webapp.utils.iiif.gen_html import gen_btn
from app.webapp.utils.logger import log


@admin.register(Digitization)
class DigitizationAdmin(UnregisteredAdmin):
    # Class for list display and search features
    search_fields = ("witness",)
    list_per_page = 100
    list_display = (
        "thumbnail",
        "witness",
        "get_nb_pages",
        # todo btn to open mirador + nb of annotations + is validated or not
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
    extra = 1  # Display only one empty form in the parent form
    max_num = 5
    readonly_fields = ("digit_preview", "view_digit", "view_anno")

    fields = ["digit_type", "pdf", "manifest", "images"]

    def digit_url(self):
        return f"/{APP_NAME}-admin/{WEBAPP_NAME}/digitization"

    @admin.display(description=get_name("Digitization"))
    def digit_preview(self, obj: Digitization):
        txt = "Manage images" if APP_LANG == "en" else "Gérer les images"
        return mark_safe(
            f'<a href="{self.digit_url()}/?q={obj.id}" target="_blank">{IIIF_ICON} {txt}</a>'
        )

    @admin.display(description=get_name("view_digit"))
    def view_digit(self, obj):
        digit = Digitization.objects.filter(pk=obj.id).first()
        if digit and digit.has_images():
            if digit.has_annotations():
                return mark_safe(
                    "<br><br>".join(
                        gen_btn(anno, "view") for anno in digit.get_annotations()
                    )
                )
            return gen_btn(digit, "view")
        return "-"

    @admin.display(description=get_name("view_anno"))
    def view_anno(self, obj):
        digit = Digitization.objects.filter(pk=obj.id).first()
        if digit and digit.has_annotations():
            anno_btn = []
            for anno in digit.get_annotations():
                action = "final" if anno.is_validated else "edit"
                anno_btn.append(gen_btn(anno, action))
            return mark_safe("<br><br>".join(anno_btn))
        return "-"

    def get_fields(self, request, obj: Witness = None):
        fields = list(super(DigitizationInline, self).get_fields(request, obj))

        # PROBLEM the issue here is that obj is a Witness and not a Digitization
        # thus all inline forms are treated identically
        if obj and obj.has_images():
            fields.append("view_digit")
            if obj.has_annotations():
                fields.append("view_anno")

        return list(set(fields))
