import nested_admin
from django.contrib import admin
from django.utils.safestring import mark_safe

from app.config.settings import APP_NAME, WEBAPP_NAME, APP_LANG
from app.webapp.admin import UnregisteredAdmin
from app.webapp.models.digitization import Digitization, get_name
from app.webapp.models.utils.constants import IMG
from app.webapp.utils.functions import gen_thumbnail, cls
from app.webapp.utils.iiif import gen_iiif_url, IIIF_ICON
from app.webapp.utils.iiif.gen_html import gen_btn


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

    fields = [
        "digit_type",
        "image",
        "pdf",
        "manifest",
    ]

    def digit_url(self):
        return f"/{APP_NAME}-admin/{WEBAPP_NAME}/digitization"

    @admin.display(description=get_name("Digitization"))
    def digit_preview(self, obj: Digitization):
        txt = "Manage images" if APP_LANG == "en" else "Gérer les images"
        return mark_safe(
            f'<a href="{self.digit_url()}/?q={obj.id}" target="_blank">{IIIF_ICON} {txt}</a>'
        )

    @admin.display(description=get_name("view_digit"))
    def view_digit(self, obj: Digitization):
        # here access to Mirador without annotation
        if obj.id:
            action = "view" if obj.has_manifest() else "no_manifest"
            return gen_btn(self, action)
        return "-"

    @admin.display(description=get_name("view_anno"))
    def view_anno(self, obj: Digitization):
        # TODO here multiple button for multiple annotation
        if obj.id and obj.has_images():
            action = "final" if obj.is_validated else "edit"
            if not obj.has_annotations():
                return gen_btn(obj, action)

            anno_btn = []
            for anno in obj.get_annotations():
                anno_btn.append(gen_btn(anno, action))
            return "<br>".join(anno_btn)
        return "-"

    # def has_view_or_change_permission(self, request, obj=None):
    #     # TODO check what does it do
    #     return False

    def get_fields(self, request, obj: Digitization = None):
        # TODO if obj + has_manifest: add manifest links
        fields = list(super(DigitizationInline, self).get_fields(request, obj))

        # if request.method == "POST" and self.wit_type() == VOL: # NOTE old version
        #     fields.append("image") # check what was the purpose

        if obj and obj.has_images():
            fields.append("view_digit")
            if obj.has_annotations():
                fields.append("view_anno")

        return list(set(fields))

    # def get_fields(self, request, obj=None):
    #     fields = list(super(WitnessInline, self).get_fields(request, obj))
    #     exclude_set = set()
    #     if not obj:  # obj will be None on the add page, and something on change pages
    #         exclude_set.add("view_digit")
    #         exclude_set.add("view_anno")
    #     return [f for f in fields if f not in exclude_set]


# class DigitizationNestedInline(DigitizationInline):
#     model = Digitization
