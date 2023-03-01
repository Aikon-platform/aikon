import nested_admin
from admin_extra_buttons.mixins import ExtraButtonsMixin

from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from vhsapp.models.models import (
    Printed,
    Volume,
    Manuscript,
    DigitizedVersion,
    Author,
    Work,
)

from vhsapp.models.digitization import (
    ImageVolume,
    PdfVolume,
    ImageManuscript,
    PdfManuscript,
    ManifestManuscript,
    ManifestVolume,
)

from vhsapp.utils.iiif import (
    IIIF_ICON,
)


@admin.register(ImageVolume)
class ImageVolumeAdmin(admin.ModelAdmin):
    list_display = (
        "image",
        "thumbnail",
    )
    search_fields = ("=volume__id", "=image")
    autocomplete_fields = ("volume",)
    list_per_page = 100

    def thumbnail(self, obj):
        return format_html(
            '<a href="{}" target="_blank">{}</a>'.format(
                "http://localhost/iiif/2/"
                + obj.image.name.split("/")[-1]
                + "/full/full/0/default.jpg",
                '<img src ="{}" width ="30" style="border-radius:50%;">'.format(
                    obj.image.url
                ),
            )
        )

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index
        """
        return {}


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
            f'<a href="/{iiif_manage_url}/?q={obj.volume.id}" target="_blank">Manage {IIIF_ICON}</a>'
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


class PdfVolumeInline(nested_admin.NestedStackedInline):
    model = PdfVolume
    extra = 1
    max_num = 1


class ManifestVolumeInline(nested_admin.NestedStackedInline):
    model = ManifestVolume
    extra = 1
    max_num = 1


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
        return format_html(
            '<a href="{}" target="_blank">{}</a>'.format(
                "http://localhost/iiif/2/"
                + obj.image.name.split("/")[-1]
                + "/full/full/0/default.jpg",
                '<img src ="{}" width ="30" style="border-radius:50%;">'.format(
                    obj.image.url
                ),
            )
        )

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index
        """
        return {}


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
            '<a href="/vhs-admin/vhsapp/imagemanuscript/?q='
            + str(obj.manuscript.id)
            + '" target="_blank">Cliquez ici pour gérer les images de ce manuscrit '
            '<img alt="IIIF" src="https://iiif.io/assets/images/logos/logo-sm.png" height="15"/></a>'
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
