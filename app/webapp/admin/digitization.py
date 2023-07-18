import nested_admin
from django.contrib import admin
from django.utils.safestring import mark_safe

from app.config.settings import APP_NAME, WEBAPP_NAME
from app.webapp.admin import UnregisteredAdmin
from app.webapp.models.digitization import Digitization, get_name
from app.webapp.models.utils.constants import IMG, MS_ABBR, IMG_ABBR, PDF_ABBR, MAN_ABBR
from app.webapp.utils.constants import MANIFEST_V2, MANIFEST_V1
from app.webapp.utils.functions import gen_thumbnail, get_img_prefix
from app.webapp.utils.iiif import gen_iiif_url, IIIF_ICON
from app.webapp.utils.iiif.annotation import has_annotations
from app.webapp.utils.iiif.gen_html import gen_btn
from app.webapp.utils.iiif.manifest import has_manifest


@admin.register(Digitization)
class DigitizationAdmin(UnregisteredAdmin):
    # NOTE useful class for list and search features
    search_fields = ("witness",)
    list_per_page = 100

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.list_display = (
            "thumbnail",
            "witness",  # show witness __str__()
            "witness__page_nb",
            # todo btn to see digit + nb of annotations + is valideted or not
        )

    def thumbnail(self, obj: Digitization):
        if obj.digit_type == IMG:
            return gen_thumbnail(
                gen_iiif_url(obj.image.name.split("/")[-1]), obj.image.url
            )
        # TODO for other types


############################
#          INLINE          #
############################


class DigitizationInline(nested_admin.NestedStackedInline):
    model = Digitization
    extra = 1  # Display only one empty form in the parent form
    max_num = 5  # TODO change naming convention to allow multiple digitizations
    readonly_fields = ("digit_preview", "manifest_v1", "manifest_v2")

    fields = [
        "digit_type",
        "image",
        "pdf",
        "manifest",
        # "manifest_v1",
        # "manifest_v2",
        # "manifest_final",
    ]

    def obj_id(self, obj):
        return obj.witness.id

    def digit_url(self):
        return f"/{APP_NAME}-admin/{WEBAPP_NAME}/digitization"

    def digit_preview(self, obj: Digitization):
        # TODO, do not display when there is None because the digitization is not image files
        return mark_safe(
            f'<a href="{self.digit_url()}/?q={self.obj_id(obj)}" target="_blank">{IIIF_ICON} Gérer les images</a>'
        )

    digit_preview.short_description = "Digitization"

    def has_view_or_change_permission(self, request, obj=None):
        # TODO check what does it do
        return False

    def get_fields(self, request, obj: Digitization = None):
        # TODO if obj + has_manifest: add manifest links
        fields = list(super(DigitizationInline, self).get_fields(request, obj))

        # if request.method == "POST" and self.wit_type() == VOL: # NOTE old version
        #     fields.append("image") # check what was the purpose

        return list(set(fields))

    @admin.display(description=get_name("manifest_v1"))
    def manifest_v1(self, obj, wit_abbr=MS_ABBR):
        if obj.id:
            img_prefix = get_img_prefix(obj, wit_abbr)
            action = "view" if has_manifest(img_prefix) else "no_manifest"
            return gen_btn(obj.id, action, MANIFEST_V1, self.wit_name().lower())
        return "-"

    @admin.display(description=get_name("manifest_v2"))
    def manifest_v2(self, obj: Digitization, wit_type=MS_ABBR):
        if obj.id:
            action = "final" if obj.manifest_final else "edit"
            if not has_annotations(obj, wit_type):
                action = "no_anno"
            return gen_btn(obj.id, action, MANIFEST_V2, self.wit_name().lower())
        return "-"

    # manifest_v2.admin_order_field = (
    #     "-author__name"  # By what value to order this column in the admin list view
    # )
    # def get_fields(self, request, obj=None):
    #     fields = list(super(WitnessInline, self).get_fields(request, obj))
    #     exclude_set = set()
    #     if not obj:  # obj will be None on the add page, and something on change pages
    #         exclude_set.add("manifest_v1")
    #         exclude_set.add("manifest_v2")
    #         exclude_set.add("manifest_final")
    #     return [f for f in fields if f not in exclude_set]


# class DigitizationNestedInline(DigitizationInline):
#     model = Digitization
