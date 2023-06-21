import nested_admin

from django.contrib import admin
from django.utils.safestring import mark_safe

from app.webapp.models.digitization import (
    ImageVolume,
    PdfVolume,
    ImageManuscript,
    PdfManuscript,
    ManifestManuscript,
    ManifestVolume,
)
from app.webapp.models.utils.constants import MS, VOL
from app.webapp.utils.iiif import gen_iiif_url
from app.webapp.utils.iiif import IIIF_ICON
from app.config.settings import APP_NAME

from app.webapp.utils.functions import (
    gen_thumbnail,
)

img_vol = f"/{APP_NAME}-admin/vhsapp/imagevolume"  # TODO change that
img_ms = f"/{APP_NAME}-admin/vhsapp/imagemanuscript"  # TODO: change that


class ImageAdmin(admin.ModelAdmin):
    class Meta:
        abstract = True

    list_per_page = 100

    def wit_type(self):
        return "witness"

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.list_display = (
            "image",
            "thumbnail",
        )
        self.search_fields = (f"={self.wit_type()}__id", "=image")
        self.autocomplete_fields = (f"{self.wit_type()}",)

    def thumbnail(self, obj):
        return gen_thumbnail(gen_iiif_url(obj.image.name.split("/")[-1]), obj.image.url)

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index
        """
        return {}


@admin.register(ImageVolume)
class ImageVolumeAdmin(ImageAdmin):
    def wit_type(self):
        return VOL


@admin.register(ImageManuscript)
class ImageManuscriptAdmin(ImageAdmin):
    def wit_type(self):
        return MS


############################
#          INLINE          #
############################


class DigitInline(admin.StackedInline):
    class Meta:
        abstract = True

    extra = 1
    max_num = 1


class PdfManuscriptInline(DigitInline):
    model = PdfManuscript


class ManifestManuscriptInline(DigitInline):
    model = ManifestManuscript


class PdfVolumeInline(nested_admin.NestedStackedInline, DigitInline):
    model = PdfVolume


class ManifestVolumeInline(nested_admin.NestedStackedInline, DigitInline):
    model = ManifestVolume


class ImageInline(DigitInline):
    class Meta:
        abstract = True

    class Media:
        css = {"all": ("css/style.css",)}
        js = ("fontawesomefree/js/all.min.js",)

    readonly_fields = ("image_preview",)

    def obj_id(self, obj):
        return None

    def img_dir(self):
        return "/"

    def wit_type(self):
        return MS if MS in self.img_dir() else VOL

    def image_preview(self, obj):
        # TODO, do not display when there is None because the digitization is not images files
        return mark_safe(
            f'<a href="{self.img_dir()}/?q={self.obj_id(obj)}" target="_blank">{IIIF_ICON} Gérer les images</a>'
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
        if request.method == "POST" and self.wit_type() == VOL:
            fields.append("image")

        return list(set(fields))


class ImageVolumeInline(nested_admin.NestedStackedInline, ImageInline):
    model = ImageVolume

    def obj_id(self, obj):
        return obj.volume.id

    def img_dir(self):
        return img_vol


class ImageManuscriptInline(ImageInline):
    model = ImageManuscript

    def obj_id(self, obj):
        return obj.manuscript.id

    def img_dir(self):
        return img_ms
