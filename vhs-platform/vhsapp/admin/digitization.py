import nested_admin

from django.contrib import admin, messages
from django.utils.safestring import mark_safe

from vhsapp.models.digitization import (
    ImageVolume,
    PdfVolume,
    ImageManuscript,
    PdfManuscript,
    ManifestManuscript,
    ManifestVolume,
)

from vhsapp.utils.iiif import IIIF_ICON, gen_img_url

from vhsapp.utils.functions import (
    gen_thumbnail,
)

img_vol = "vhs-admin/vhsapp/imagevolume"  # TODO change that
img_ms = "/vhs-admin/vhsapp/imagemanuscript"  # TODO: change that


@admin.register(ImageVolume)
class ImageVolumeAdmin(admin.ModelAdmin):
    list_display = ("image", "thumbnail")
    search_fields = ("=volume__id", "=image")
    autocomplete_fields = ("volume",)
    list_per_page = 100

    def thumbnail(self, obj):
        return gen_thumbnail(gen_img_url(obj.image.name.split("/")[-1]), obj.image.url)

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index
        """
        return {}


@admin.register(ImageManuscript)
class ImageManuscriptAdmin(admin.ModelAdmin):
    list_display = (
        "image",
        "thumbnail",
    )
    search_fields = ("=manuscript__id", "=image")
    autocomplete_fields = ("manuscript",)
    list_per_page = 100

    def thumbnail(self, obj):
        return gen_thumbnail(gen_img_url(obj.image.name.split("/")[-1]), obj.image.url)

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index
        """
        return {}


############################
#          INLINE          #
############################


class ImageVolumeInline(nested_admin.NestedStackedInline):
    class Media:
        css = {"all": ("css/style.css",)}
        js = ("fontawesomefree/js/all.min.js",)

    model = ImageVolume
    extra = 1
    max_num = 1
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        return mark_safe(
            f'<a href="/{img_vol}/?q={obj.volume.id}" target="_blank">Manage {IIIF_ICON}</a>'
        )

    image_preview.short_description = "Images"

    def has_view_or_change_permission(self, request, obj=None):
        return False

    def get_fields(self, request, obj=None):
        fields = list(super(ImageVolumeInline, self).get_fields(request, obj))
        if not obj:  # obj will be None on the add page, and something on change pages
            fields.remove("image_preview")
        else:
            fields.remove("image")
        if request.method == "POST":
            fields.append("image")
        fields = list(set(fields))

        return fields


class ImageManuscriptInline(admin.StackedInline):
    class Media:
        css = {"all": ("css/style.css",)}
        js = ("fontawesomefree/js/all.min.js",)

    model = ImageManuscript
    extra = 1
    max_num = 1
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        return mark_safe(
            f'<a href="/{img_ms}/?q={obj.manuscript.id}" target="_blank">Manage {IIIF_ICON}</a>'
        )

    image_preview.short_description = "Images"

    def has_view_or_change_permission(self, request, obj=None):
        return False

    def get_fields(self, request, obj=None):
        fields = list(super(ImageManuscriptInline, self).get_fields(request, obj))
        exclude_set = set()
        if not obj:  # obj will be None on the add page, and something on change pages
            exclude_set.add("image_preview")
        else:
            exclude_set.add("image")

        return [f for f in fields if f not in exclude_set]


class PdfManuscriptInline(admin.StackedInline):
    model = PdfManuscript
    extra = 1
    max_num = 1


class ManifestManuscriptInline(admin.StackedInline):
    model = ManifestManuscript
    extra = 1
    max_num = 1


class PdfVolumeInline(nested_admin.NestedStackedInline):
    model = PdfVolume
    extra = 1
    max_num = 1


class ManifestVolumeInline(nested_admin.NestedStackedInline):
    model = ManifestVolume
    extra = 1
    max_num = 1
