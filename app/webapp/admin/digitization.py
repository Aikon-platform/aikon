import nested_admin
from django.contrib import admin
from django.utils.safestring import mark_safe

from app.config.settings import APP_NAME, WEBAPP_NAME
from app.webapp.admin import UnregisteredAdmin
from app.webapp.models.digitization import Digitization
from app.webapp.utils.functions import gen_thumbnail
from app.webapp.utils.iiif import gen_iiif_url, IIIF_ICON


@admin.register(Digitization)
class DigitizationAdmin(UnregisteredAdmin):
    search_fields = ("witness",)

    list_per_page = 100

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.list_display = (
            # "image",
            "thumbnail",
        )
        self.search_fields = (f"=witness__id", "=image")
        self.autocomplete_fields = (f"witness",)

    def thumbnail(self, obj):
        # FOR IMAGES WHERE obj = Digitization (?)
        return gen_thumbnail(gen_iiif_url(obj.image.name.split("/")[-1]), obj.image.url)


############################
#          INLINE          #
############################


class DigitizationInline(admin.StackedInline):
    class Media:
        css = {"all": ("css/style.css",)}
        js = ("fontawesomefree/js/all.min.js",)

    model = Digitization
    extra = 1
    max_num = 1
    readonly_fields = ("digit_preview",)

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

    def get_fields(self, request, obj=None):
        # TODO check what does it do
        fields = list(super(DigitizationInline, self).get_fields(request, obj))
        if not obj:  # obj will be None on the add page, and something on change pages
            fields.remove("digit_preview")
        else:
            fields.remove("image")
        # if request.method == "POST" and self.wit_type() == VOL: # NOTE old version
        if request.method == "POST":
            fields.append("image")

        return list(set(fields))


class DigitizationNestedInline(nested_admin.NestedStackedInline, DigitizationInline):
    model = Digitization
