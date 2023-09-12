import nested_admin
from django.contrib import admin
from django.utils.safestring import mark_safe

from app.config.settings import APP_NAME, WEBAPP_NAME, APP_LANG
from app.webapp.admin import UnregisteredAdmin
from app.webapp.models import get_wit_abbr
from app.webapp.models.digitization import Digitization, get_name
from app.webapp.models.utils.constants import IMG, MS_ABBR, IMG_ABBR, PDF_ABBR, MAN_ABBR
from app.webapp.utils.constants import MANIFEST_V2, MANIFEST_V1
from app.webapp.utils.functions import gen_thumbnail, get_img_prefix, anno_btn
from app.webapp.utils.iiif import gen_iiif_url, IIIF_ICON
from app.webapp.utils.iiif.gen_html import gen_btn, gen_manifest_btn
from app.webapp.utils.iiif.manifest import has_manifest


@admin.register(Digitization)
class DigitizationAdmin(UnregisteredAdmin):
    # NOTE useful class for list and search features
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
    readonly_fields = ("digit_preview", "manifest_v1", "manifest_v2")

    fields = [
        "digit_type",
        "image",
        "pdf",
        "manifest",
        # "manifest_v1",
        # "manifest_v2",
    ]

    def digit_url(self):
        return f"/{APP_NAME}-admin/{WEBAPP_NAME}/digitization"

    @admin.display(description=get_name("Digitization"))
    def digit_preview(self, obj: Digitization):
        txt = "Manage images" if APP_LANG == "en" else "Gérer les images"
        return mark_safe(
            f'<a href="{self.digit_url()}/?q={obj.id}" target="_blank">{IIIF_ICON} {txt}</a>'
        )

    # def has_view_or_change_permission(self, request, obj=None):
    #     # TODO check what does it do
    #     return False

    def get_fields(self, request, obj: Digitization = None):
        # TODO if obj + has_manifest: add manifest links
        fields = list(super(DigitizationInline, self).get_fields(request, obj))

        # if request.method == "POST" and self.wit_type() == VOL: # NOTE old version
        #     fields.append("image") # check what was the purpose

        return list(set(fields))

    @admin.display(description=get_name("manifest_v1"))
    def manifest_v1(self, obj: Digitization):
        if obj.id:
            action = "view" if obj.has_manifest() else "no_manifest"
            return gen_btn(obj.id, action, MANIFEST_V1, obj.get_wit_type())
        return "-"

    @admin.display(description=get_name("manifest_v2"))
    def manifest_v2(self, obj: Digitization):
        wit_abbr = get_wit_abbr(obj.get_wit_type())
        if obj.id and has_manifest(get_img_prefix(obj, wit_abbr)):
            action = "final" if obj.is_validated else "edit"
            if not obj.has_annotations():
                action = "no_anno"
            return gen_btn(obj.id, action, MANIFEST_V2, obj.get_wit_type())
        return "-"

    # def get_fields(self, request, obj=None):
    #     fields = list(super(WitnessInline, self).get_fields(request, obj))
    #     exclude_set = set()
    #     if not obj:  # obj will be None on the add page, and something on change pages
    #         exclude_set.add("manifest_v1")
    #         exclude_set.add("manifest_v2")
    #     return [f for f in fields if f not in exclude_set]


# class DigitizationNestedInline(DigitizationInline):
#     model = Digitization
