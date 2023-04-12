import nested_admin

from django.contrib import admin
from django.utils.safestring import mark_safe

from vhsapp.models.digitization import (
    ImageVolume,
    PdfVolume,
    ImageManuscript,
    PdfManuscript,
    ManifestManuscript,
    ManifestVolume,
)

from vhsapp.utils.iiif import IIIF_ICON, gen_iiif_url
from vhsapp.utils.constants import APP_NAME
from vhsapp.models.constants import MS, VOL, WIT

from vhsapp.utils.functions import (
    gen_thumbnail,
)


class ImageAdmin(admin.ModelAdmin):
    class Meta:
        abstract = True

    list_per_page = 100
    wit_type = WIT

    def get_wit_type(self):
        return self.wit_type

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.list_display = (
            "image",
            "thumbnail",
        )
        self.search_fields = (f"={WIT}__id", "=image")
        self.autocomplete_fields = (f"{WIT}",)

    def thumbnail(self, obj):
        return gen_thumbnail(gen_iiif_url(obj.image.name.split("/")[-1]), obj.image.url)

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index
        """
        return {}


@admin.register(ImageVolume)
class ImageVolumeAdmin(ImageAdmin):
    wit_type = VOL


@admin.register(ImageManuscript)
class ImageManuscriptAdmin(ImageAdmin):
    wit_type = MS


############################
#          INLINE          #
############################


class DigitInline(admin.StackedInline):
    class Meta:
        abstract = True

    extra = 1
    max_num = 1
    wit_type = WIT

    def get_wit_type(self):
        return self.wit_type


class PdfManuscriptInline(DigitInline):
    model = PdfManuscript
    wit_type = MS


class ManifestManuscriptInline(DigitInline):
    model = ManifestManuscript
    wit_type = MS


class PdfVolumeInline(nested_admin.NestedStackedInline, DigitInline):
    model = PdfVolume
    wit_type = VOL


class ManifestVolumeInline(nested_admin.NestedStackedInline, DigitInline):
    model = ManifestVolume
    wit_type = VOL


class ImageInline(DigitInline):
    class Meta:
        abstract = True

    class Media:
        css = {"all": ("css/style.css",)}
        js = ("fontawesomefree/js/all.min.js",)

    readonly_fields = ("image_preview",)
    wit_type = WIT

    def obj_id(self, obj):
        return obj.witness.id

    def img_url(self):
        return (
            f"/{APP_NAME}-admin/vhsapp/image{self.get_wit_type()}"  # TODO change that
        )

    def get_wit_type(self):
        return self.wit_type

    def image_preview(self, obj):
        # TODO, do not display when there is None because the digitization is not images files
        return mark_safe(
            f'<a href="{self.img_url()}/?q={self.obj_id(obj)}" target="_blank">{IIIF_ICON} Gérer les images</a>'
        )

    image_preview.short_description = "Images"

    def has_view_or_change_permission(self, request, obj=None):
        return False

    def get_fields(self, request, obj=None):
        fields = list(super(ImageInline, self).get_fields(request, obj))
        if not obj:  # obj will be None on the add page, and something on change pages
            fields.remove("image_preview")
        else:
            fields.remove("image")
        if request.method == "POST" and self.get_wit_type() == "volume":
            fields.append("image")

        return list(set(fields))


class ImageVolumeInline(nested_admin.NestedStackedInline, ImageInline):
    model = ImageVolume
    wit_type = VOL


class ImageManuscriptInline(ImageInline):
    model = ImageManuscript
    wit_type = MS
