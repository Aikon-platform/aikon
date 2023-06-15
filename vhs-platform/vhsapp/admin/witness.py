import glob
import zipfile

import nested_admin
from admin_extra_buttons.decorators import button
from admin_extra_buttons.mixins import ExtraButtonsMixin

from django.contrib import admin, messages
from django.http import HttpResponse, HttpResponseRedirect
from django.template.defaultfilters import truncatewords_html
from django.utils.safestring import mark_safe

from vhsapp.admin.admin import AuthorFilter, WorkFilter, DescriptiveElementsFilter

from vhsapp.models.witness import (
    Printed,
    Volume,
    Manuscript,
)

from vhsapp.models.constants import MS, VOL, WIT, MS_ABBR, VOL_ABBR, WIT_ABBR

from vhsapp.admin.digitization import (
    PdfManuscriptInline,
    ManifestManuscriptInline,
    ImageManuscriptInline,
    PdfVolumeInline,
    ManifestVolumeInline,
    ImageVolumeInline,
)

from vhsapp.utils.constants import (
    SITE_HEADER,
    SITE_TITLE,
    SITE_INDEX_TITLE,
    TRUNCATEWORDS,
    MAX_ITEMS,
    MANIFEST_AUTO,
    MANIFEST_V2,
)

from vhsapp.utils.iiif import gen_iiif_url
from vhsapp.utils.iiif.annotation import has_annotations
from vhsapp.utils.iiif.manifest import has_manifest, gen_manifest_url

from vhsapp.utils.iiif.gen_html import (
    get_link_manifest,
    gen_btn,
    gen_manifest_btn,
)
from vhsapp.utils.functions import (
    list_to_txt,
    zip_img,
    get_file_list,
    get_pdf_imgs,
    get_icon,
    anno_btn,
)
from vhsapp.utils.logger import console, log


def get_img_prefix(obj, wit_abbr=MS_ABBR):
    wit_type = MS.lower() if wit_abbr == MS_ABBR else VOL.lower()
    # TODO, generalize that to make it work for every type of digitization
    if hasattr(obj, f"pdf{wit_type}_set"):
        if pdf_obj := getattr(obj, f"pdf{wit_type}_set").first():
            return pdf_obj.pdf.name.split("/")[-1].split(".")[0]
    return f"{wit_abbr}{obj.id}"


class ManifestAdmin(admin.ModelAdmin):
    class Meta:
        abstract = True

    readonly_fields = ("manifest_auto", "manifest_v2")

    def wit_name(self):
        return MANIFEST_AUTO

    def is_annotated(self, obj, wit_abbr=MS_ABBR):
        action = "FINAL" if obj.manifest_final else "EDIT"
        return mark_safe(
            anno_btn(
                obj.id,
                action if has_annotations(obj, wit_abbr) else "NO ANNOTATION YET",
            )
        )

    is_annotated.short_description = "Annotation"

    def manifest_link(self, obj, wit_abbr=MS_ABBR):
        wit_type = MS if wit_abbr == MS_ABBR else VOL
        return gen_manifest_btn(
            obj.id, wit_type, has_manifest(get_img_prefix(obj, wit_abbr))
        )
        # if has_manifest(get_img_prefix(obj, wit_abbr)):
        #     manifest = gen_manifest_url(obj.id, MANIFEST_AUTO, wit_type.lower())
        #     return mark_safe(get_link_manifest(obj.id, manifest, "iiif_auto_"))
        # return "No manifest"

    manifest_link.short_description = "IIIF manifest"

    def manifest_auto(self, obj, wit_abbr=MS_ABBR):
        if obj.id:
            img_prefix = get_img_prefix(obj, wit_abbr)
            action = "VISUALIZE" if has_manifest(img_prefix) else "NO MANIFEST"
            return gen_btn(obj.id, action, MANIFEST_AUTO, self.wit_name().lower())
        return "-"

    manifest_auto.short_description = "Manifeste (automatique)"

    def manifest_v2(self, obj, wit_type=MS_ABBR):
        if obj.id:
            action = "FINAL" if obj.manifest_final else "EDIT"
            if not has_annotations(obj, wit_type):
                action = "NO ANNOTATION YET"
            return gen_btn(obj.id, action, MANIFEST_V2, self.wit_name().lower())
        return "-"

    manifest_v2.short_description = "Manifeste (modifiable)"


class VolumeInline(nested_admin.NestedStackedInline):
    model = Volume
    fields = [
        "manifest_auto",
        "manifest_v2",
        "manifest_final",
        "title",
        "number_identifier",
        "place",
        "date",
        "publishers_booksellers",
        "digitized_version",
        "comment",
        "other_copies",
    ]
    autocomplete_fields = ("digitized_version",)
    extra = 0
    classes = ("collapse",)
    inlines = [PdfVolumeInline, ManifestVolumeInline, ImageVolumeInline]

    def wit_name(self):
        return VOL

    def get_fields(self, request, obj=None):
        fields = list(super(VolumeInline, self).get_fields(request, obj))
        exclude_set = set()
        if not obj:  # obj will be None on the add page, and something on change pages
            exclude_set.add("manifest_auto")
            exclude_set.add("manifest_v2")
            exclude_set.add("manifest_final")
        return [f for f in fields if f not in exclude_set]

    # TODO use Abstract Model ManifestAdmin instead
    readonly_fields = ("manifest_auto", "manifest_v2")

    def manifest_auto(self, obj):
        if obj.id:
            img_prefix = get_img_prefix(obj, VOL_ABBR)
            action = "VISUALIZE" if has_manifest(img_prefix) else "NO MANIFEST"
            return gen_btn(obj.id, action, MANIFEST_AUTO, self.wit_name().lower())
        return "-"

    manifest_auto.short_description = "Manifeste (automatique)"

    def manifest_v2(self, obj):
        if obj.id:
            action = "FINAL" if obj.manifest_final else "EDIT"
            if not has_annotations(obj, VOL_ABBR):
                action = "NO ANNOTATION YET"
            return gen_btn(obj.id, action, MANIFEST_V2, self.wit_name().lower())
        return "-"

    manifest_v2.short_description = "Manifeste (modifiable)"


@admin.register(Volume)
class VolumeAdmin(admin.ModelAdmin):
    search_fields = ("title",)

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index
        """
        return {}


class WitnessAdmin(ExtraButtonsMixin, admin.ModelAdmin):
    class Meta:
        verbose_name = "Witness"
        verbose_name_plural = "Witnesses"
        abstract = True

    class Media:
        css = {"all": ("css/style.css",)}
        js = ("js/jquery-3.6.1.js", "js/script.js")

    # NOTE: attribute to use to change to template of witness (template at: templates/admin/change.html)
    # change_form_template = "admin/change.html"

    ordering = ("id",)
    # list_filter = (AuthorFilter, WorkFilter)
    # autocomplete_fields = ("author", "work")
    list_per_page = 100
    exclude = ("slug", "created_at", "updated_at")

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.actions = [
            "export_selected_manifests",
            "export_selected_iiif_images",
            "export_selected_images",
            "export_selected_pdfs",
        ]
        if self.wit_type() == VOL:
            self.actions += ["detect_similarity"]

    def wit_type(self):
        return "witness"

    def short_author(self, obj):
        return truncatewords_html(obj.author, TRUNCATEWORDS)

    short_author.short_description = "Auteurs et/ou Éditeurs"

    def short_work(self, obj):
        return truncatewords_html(obj.work, TRUNCATEWORDS)

    short_work.short_description = "Titre de l'œuvre"

    def check_selection(self, queryset, request):
        if len(queryset) > MAX_ITEMS:
            self.message_user(
                request,
                f"Actions can be performed on up to {MAX_ITEMS} elements only.",
                messages.WARNING,
            )
            return True
        return False

    def get_img_list(self, queryset, with_img=True, with_pdf=True):
        results = queryset.exclude()
        result_list = []
        wit_type = self.wit_type()

        if with_img:
            field_tag = (
                f"{wit_type}__image{wit_type}__image"
                if wit_type == VOL.lower()
                else f"image{wit_type}__image"
            )
            img_list = results.values_list(field_tag, flat=True)
            img_list = [img.split("/")[-1] for img in img_list if img is not None]
            result_list = result_list + img_list

        if with_pdf:
            field_tag = (
                f"{wit_type}__pdf{wit_type}__pdf"
                if wit_type == VOL.lower()
                else f"pdf{wit_type}__pdf"
            )
            pdf_list = results.values_list(field_tag, flat=True)
            pdf_list = [pdf.split("/")[-1] for pdf in pdf_list if pdf is not None]
            result_list = result_list + get_pdf_imgs(pdf_list, wit_type)

        return result_list

    def save_file(self, request, obj):
        # instantiated by inheritance (following code is fake)
        files = request.FILES.getlist("imagewitness_set-0-image")
        for file in files[:-1]:
            obj.imagewitness_set.create(image=file)

    def save_model(self, request, obj, form, change):
        if not obj.user:
            obj.user = request.user
        obj.save()
        messages.warning(
            request,
            "Le processus de conversion de.s fichier.s PDF en images et/ou d'extraction des images à partir de "
            "manifeste.s externe.s est en cours. Veuillez patienter quelques instants pour corriger "
            "les annotations automatiques.",
        )
        self.save_file(request, obj)

    @admin.action(description="Exporter les images IIIF sélectionnées")
    def export_selected_iiif_images(self, request, queryset):
        img_list = [gen_iiif_url(img) for img in self.get_img_list(queryset)]
        return list_to_txt(img_list, f"IIIF_images")

    # @admin.action(description="Exporter les images sélectionnées")
    # def export_selected_images(self, request, queryset):
    #     if self.check_selection(queryset, request):
    #         return HttpResponseRedirect(request.get_full_path())
    #     # NOTE get_file_list(IMG_PATH, self.get_img_list(queryset)) is returning None
    #     return zip_img(zipfile, get_file_list(IMG_PATH, self.get_img_list(queryset)))

    # @admin.action(description="Exporter les documents PDF sélectionnés")
    # def export_selected_pdfs(self, request, queryset):
    #     if self.check_selection(queryset, request):
    #         return HttpResponseRedirect(request.get_full_path())
    #     return zip_img(
    #         zipfile, self.get_img_list(queryset, with_img=False, with_pdf=True), "pdf"
    #     )

    @button(
        permission="demo.add_demomodel1",
        change_form=False,
        html_attrs={"style": "background-color:#88FF88;color:black"},
    )
    def exporter_images(self, request):
        return HttpResponseRedirect(
            "https://iscd.huma-num.fr/media/images_vhs.zip"
        )  # TODO CHANGE THAT


@admin.register(Printed)
class PrintedAdmin(WitnessAdmin, nested_admin.NestedModelAdmin, admin.SimpleListFilter):
    list_display = (
        "short_author",
        "short_work",
        "place",
        "date",
        "publishers_booksellers",
        "published",
    )
    list_editable = ("date",)
    search_fields = ("author__name", "work__title", "descriptive_elements")
    list_filter = (AuthorFilter, WorkFilter, DescriptiveElementsFilter)
    fieldsets = (
        (
            "Chaque œuvre correspond à une édition donnée de cette œuvre",
            {
                "fields": (
                    "author",
                    "work",
                    "place",
                    "date",
                    "publishers_booksellers",
                    "description",
                    "descriptive_elements",
                    "illustrators",
                    "engravers",
                    "published",
                )
            },
        ),
    )
    inlines = [VolumeInline]

    def wit_type(self):
        return "print"

    def save_file(self, request, obj):
        # TODO: check if needed for Volume
        files = request.FILES.getlist("imagevolume_set-0-image")
        for file in files[:-1]:
            obj.imagevolume_set.create(image=file)

    def save_related(self, request, form, formsets, change):
        super(PrintedAdmin, self).save_related(request, form, formsets, change)
        count_volumes = form.instance.volume_set.count()
        for i in range(count_volumes):
            files = request.FILES.getlist(f"volume_set-{i}-imagevolume_set-0-image")
            for file in files[:-1]:
                form.instance.volume_set.all()[i].imagevolume_set.create(image=file)

    @admin.action(description="Exporter les manifests IIIF sélectionnés")
    def export_selected_manifests(self, request, queryset):
        results = queryset.exclude(volume__isnull=True).values_list(
            "volume__id", "volume__manifestvolume__manifest"
        )
        manifests = [gen_manifest_url(mnf[0], MANIFEST_V2) for mnf in results]
        return list_to_txt(manifests, f"IIIF_manifest")


@admin.register(Manuscript)
class ManuscriptAdmin(WitnessAdmin, ManifestAdmin):
    # list of fields that are displayed in the all witnesses tab
    list_display = (
        "id",
        "reference_number",
        "conservation_place",
        "short_author",
        # "short_work",
        # "date_century",
        # "sheets",
        # "published",
        "manifest_link",
        "is_annotated",
    )
    list_display_links = ("reference_number",)
    # search_fields = ("author__name", "work__title")
    search_fields = (
        "author__name",
        "conservation_place",
        "reference_number",
        "remarks",
    )
    autocomplete_fields = ("author", "digitized_version")
    # list_editable = ("date_century",)
    inlines = [PdfManuscriptInline, ManifestManuscriptInline, ImageManuscriptInline]
    readonly_fields = ("manifest_auto", "manifest_v2")

    def wit_type(self):
        return "manuscript"

    def wit_name(self):
        return MS

    def save_file(self, request, obj):
        files = request.FILES.getlist("imagemanuscript_set-0-image")
        for file in files[:-1]:
            obj.imagemanuscript_set.create(image=file)

    @admin.action(description="Exporter les manifests IIIF sélectionnés")
    def export_selected_manifests(self, request, queryset):
        # results = queryset.exclude(volume__isnull=True).values_list("volume__id")
        results = queryset.values_list("id", "manifestmanuscript__manifest")
        manifests = [
            gen_manifest_url(mnf[0], MANIFEST_V2, MS.lower()) for mnf in results
        ]
        return list_to_txt(manifests, "Manifest_IIIF")

    fieldsets = (
        (
            "Chaque manuscrit correspond à un exemplaire de l'œuvre",
            {
                "fields": (
                    "manifest_auto",
                    "manifest_v2",
                    "manifest_final",
                    "author",
                    # "work",
                    "conservation_place",
                    "reference_number",
                    # "date_century",
                    "date_free",
                    "sheets",
                    "origin_place",
                    "remarks",
                    "copyists",
                    "miniaturists",
                    "digitized_version",
                    "pinakes_link",
                    "published",
                )
            },
        ),
    )

    def get_fieldsets(self, request, obj=None):
        """
        Show 3 first manifest fields only if the object exists
        """
        fieldsets = super(ManuscriptAdmin, self).get_fieldsets(request, obj)
        if not obj:
            from copy import deepcopy

            exclude_fieldsets = deepcopy(fieldsets)
            exclude_fieldsets[0][1]["fields"] = exclude_fieldsets[0][1]["fields"][3:]
            return exclude_fieldsets
        return fieldsets
