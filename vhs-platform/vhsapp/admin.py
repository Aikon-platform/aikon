import csv
import io
import os
import zipfile
import requests
import PyPDF2
import environ
from pathlib import Path
from pikepdf import Pdf
from vhs import settings

import nested_admin
from admin_extra_buttons.decorators import button
from admin_extra_buttons.mixins import ExtraButtonsMixin
from admin_searchable_dropdown.filters import AutocompleteFilter

from django.contrib import admin, messages
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.template.defaultfilters import truncatewords_html
from django.shortcuts import render

from vhs.settings import VHS_APP_URL, CANTALOUPE_APP_URL, SAS_APP_URL
from vhsapp.models import (
    Printed,
    Volume,
    Manuscript,
    DigitizedVersion,
    ImageVolume,
    PdfVolume,
    ImageManuscript,
    PdfManuscript,
    Author,
    ManifestManuscript,
    ManifestVolume,
    Work,
)
from vhsapp.tasking import (
    connect_to_slurm_cluster,
    start_slurm_job,
    wait_for_job_completion,
    retrieve_result_file,
)
from vhsapp.utils.constants import (
    SITE_HEADER,
    SITE_TITLE,
    SITE_INDEX_TITLE,
    TRUNCATEWORDS,
    MAX_ITEMS,
    APP_NAME,
)
from vhsapp.utils.paths import (
    MEDIA_PATH,
    VOL_PDF_PATH,
    IMG_PATH,
    MS_PDF_PATH,
)

"""
Admin site
"""
admin.site.site_header = SITE_HEADER
admin.site.site_title = SITE_TITLE
admin.site.index_title = SITE_INDEX_TITLE

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(env_file=f"{BASE_DIR}/{APP_NAME}/.env")


class AuthorFilter(AutocompleteFilter):
    title = "Auteur"  # Display title
    field_name = "author"  # Name of the foreign key field


class WorkFilter(AutocompleteFilter):
    title = "Titre de l'oeuvre"
    field_name = "work"


class DescriptiveElementsFilter(admin.SimpleListFilter):
    # Filter options in the right sidebar
    title = "Catégorie"
    # Parameter for the filter that will be used in the URL query
    parameter_name = "category"

    def lookups(self, request, model_admin):
        return (
            ("hn", "Histoire naturelle"),
            ("sm", "Sciences mathématiques"),
        )

    def queryset(self, request, queryset):
        if self.value() == "hn":
            return queryset.filter(
                descriptive_elements__contains="Histoire naturelle",
            )
        if self.value() == "sm":
            return queryset.filter(
                descriptive_elements__contains="Sciences mathématiques",
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
                CANTALOUPE_APP_URL
                + "iiif/2/"
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
            '<a href="/vhs-admin/vhsapp/imagevolume/?q='
            + str(obj.volume.id)
            + '" target="_blank">Cliquez ici pour gérer les images de ce volume '
            '<img alt="IIIF" src="https://iiif.io/assets/images/logos/logo-sm.png" height="15"/></a>'
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
    readonly_fields = ("manifest_auto", "manifest_v2")
    autocomplete_fields = ("digitized_version",)
    extra = 0
    classes = ("collapse",)
    inlines = [PdfVolumeInline, ManifestVolumeInline, ImageVolumeInline]

    def manifest_auto(self, obj):
        if obj.id:
            url_manifest_auto = (
                f"{VHS_APP_URL}vhs/iiif/auto/volume/vol-{obj.id}/manifest.json"
            )
            link_manifest_auto = (
                '<a id="url_manifest_auto_'
                + str(obj.id)
                + '" href="/vhs/iiif/auto/volume/vol-'
                + str(obj.id)
                + '/manifest.json" target="_blank">'
                + url_manifest_auto
                + "</a> "
            )
            return mark_safe(
                link_manifest_auto
                + '<img alt="IIIF" src="https://iiif.io/assets/images/logos/logo-sm.png" height="15"/></a><br>'
                '<button id="annotate_manifest_auto_'
                + str(obj.id)
                + '" class="button" style="background-color:#EFB80B;color:white;padding:8px 10px;"><i class="fa-solid fa-eye"></i> VISUALISER ANNOTATIONS <i class="fa-solid fa-comment"></i></button><br>'
                '<a href="/vhs/iiif/auto/volume/'
                + str(obj.id)
                + '/annotation/" target="_blank"><i class="fa-solid fa-download"></i> Télécharger les annotations (CSV)</a>'
                '<span id="message_auto_'
                + str(obj.id)
                + '" style="color:#FF0000"></span>'
            )
        return "-"

    manifest_auto.short_description = "Manifeste (automatique)"

    def manifest_v2(self, obj):
        if obj.id:
            url_manifest = f"{VHS_APP_URL}vhs/iiif/v2/volume/vol-{obj.id}/manifest.json"
            link_manifest = (
                '<a id="url_manifest_'
                + str(obj.id)
                + '" href="/vhs/iiif/v2/volume/vol-'
                + str(obj.id)
                + '/manifest.json" target="_blank">'
                + url_manifest
                + "</a> "
            )
            if not obj.manifest_final:
                button = (
                    '<button id="annotate_manifest_'
                    + str(obj.id)
                    + '" class="button" style="background-color:#008CBA;color:white;padding:8px 10px;"><i class="fa-solid fa-pen-to-square"></i> ÉDITER ANNOTATIONS <i class="fa-solid fa-comment"></i></button><br>'
                )
            else:
                button = (
                    '<button id="manifest_final_'
                    + str(obj.id)
                    + '" class="button" style="background-color:#4CAF50;color:white;padding:8px 10px;"><i class="fa-solid fa-eye"></i> ANNOTATIONS FINALES <i class="fa-solid fa-comment"></i></button><br>'
                )
            return mark_safe(
                link_manifest
                + '<img alt="IIIF" src="https://iiif.io/assets/images/logos/logo-sm.png" height="15"/></a><br>'
                + button
                + '<a href="'
                + SAS_APP_URL
                + "search-api/vol-"
                + str(obj.id)
                + '/search/" target="_blank"><i class="fa-solid fa-download"></i> Télécharger les annotations (JSON)</a>'
                '<span id="message_' + str(obj.id) + '" style="color:#FF0000"></span>'
            )
        return "-"

    manifest_v2.short_description = "Manifeste (en cours de vérification)"

    def get_fields(self, request, obj=None):
        fields = list(super(VolumeInline, self).get_fields(request, obj))
        exclude_set = set()
        if not obj:  # obj will be None on the add page, and something on change pages
            exclude_set.add("manifest_auto")
            exclude_set.add("manifest_v2")
            exclude_set.add("manifest_final")
        return [f for f in fields if f not in exclude_set]


@admin.register(Printed)
class PrintedAdmin(
    ExtraButtonsMixin, nested_admin.NestedModelAdmin, admin.SimpleListFilter
):
    change_form_template = "admin/change.html"

    class Media:
        css = {"all": ("css/style.css",)}
        js = ("js/jquery-3.6.1.js", "js/script.js")

    list_display = (
        "short_author",
        "short_work",
        "place",
        "date",
        "publishers_booksellers",
        "published",
    )
    ordering = ("id",)
    list_editable = ("date",)
    search_fields = ("author__name", "work__title", "descriptive_elements")
    list_filter = (AuthorFilter, WorkFilter, DescriptiveElementsFilter)
    autocomplete_fields = ("author", "work")
    list_per_page = 100
    exclude = ("slug", "created_at", "updated_at")
    fieldsets = (
        (
            "Chaque oeuvre correspond à une édition donnée de cette oeuvre",
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
    actions = [
        "export_selected_manifests",
        "export_selected_iiif_images",
        "export_selected_images",
        "export_selected_pdfs",
        "detect_similarity",
    ]
    inlines = [VolumeInline]

    def short_author(self, obj):
        return truncatewords_html(obj.author, TRUNCATEWORDS)

    short_author.short_description = "Auteurs et/ou Éditeurs scientifiques"

    def short_work(self, obj):
        return truncatewords_html(obj.work, TRUNCATEWORDS)

    short_work.short_description = "Titre de l'oeuvre"

    def save_model(self, request, obj, form, change):
        if not obj.user:
            obj.user = request.user
        # Save the model instance
        obj.save()
        # Add a warning message
        messages.warning(
            request,
            "Le processus de conversion de.s fichier.s PDF en images et/ou d'extraction des images à partir de manifeste.s externe.s est en cours. Veuillez patienter quelques instants pour corriger les annotations automatiques.",
        )

    def save_related(self, request, form, formsets, change):
        super(PrintedAdmin, self).save_related(request, form, formsets, change)
        count_volumes = form.instance.volume_set.count()
        for i in range(count_volumes):
            files = request.FILES.getlist(f"volume_set-{i}-imagevolume_set-0-image")
            for file in files[:-1]:
                form.instance.volume_set.all()[i].imagevolume_set.create(image=file)

    @admin.action(description="Exporter les manifests IIIF des Imprimés sélectionnés")
    def export_selected_manifests(self, request, queryset):
        printed = queryset.exclude(volume__isnull=True)
        manifests_list = printed.values_list(
            "volume__id", "volume__manifestvolume__manifest"
        )
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=manifests_volumes.csv"
        writer = csv.writer(response)
        writer.writerow(["Manifest_IIIF"])
        for manifest in manifests_list:
            if mnf := manifest[1]:
                writer.writerow([mnf])
            else:
                writer.writerow(
                    [f"{VHS_APP_URL}vhs/iiif/v2/volume/vol-{manifest[0]}/manifest.json"]
                )
        return response

    @admin.action(description="Exporter les images IIIF des Imprimés sélectionnés")
    def export_selected_iiif_images(self, request, queryset):
        printed = queryset.exclude(volume__isnull=True)
        images_list = printed.values_list("volume__imagevolume__image", flat=True)
        pdfs_list = printed.values_list("volume__pdfvolume__pdf", flat=True)
        images_list = [
            image.split("/")[-1] for image in images_list if image is not None
        ]
        pdfs_list = [pdf.split("/")[-1] for pdf in pdfs_list if pdf is not None]
        pdf_images_list = []
        for pdf in pdfs_list:
            pdf_file = Pdf.open(f"{MEDIA_PATH}{VOL_PDF_PATH}{pdf}")
            total_pages = len(pdf_file.pages)
            for image_counter in range(1, total_pages + 1):
                pdf_images_list.append(pdf.replace(".pdf", f"_{image_counter:04d}.jpg"))
        all_images = images_list + pdf_images_list
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=images_iiif_volumes.csv"
        writer = csv.writer(response)
        writer.writerow(["Image_IIIF"])
        for image in all_images:
            writer.writerow(
                [f"{CANTALOUPE_APP_URL}iiif/2/{image}/full/full/0/default.jpg"]
            )
        return response

    @admin.action(description="Exporter les images des Imprimés sélectionnés")
    def export_selected_images(self, request, queryset):
        if len(queryset) > MAX_ITEMS:
            self.message_user(
                request,
                f"{MAX_ITEMS} éléments au maximum doivent être sélectionnés afin d'appliquer les actions.",
                messages.WARNING,
            )
            return HttpResponseRedirect(request.get_full_path())

        printed = queryset.exclude(volume__isnull=True)
        images_list = printed.values_list("volume__imagevolume__image", flat=True)
        pdfs_list = printed.values_list("volume__pdfvolume__pdf", flat=True)
        images_list = [
            image.split("/")[-1] for image in images_list if image is not None
        ]
        pdfs_list = [pdf.split("/")[-1] for pdf in pdfs_list if pdf is not None]
        pdf_images_list = []
        for pdf in pdfs_list:
            pdf_file = open(f"{MEDIA_PATH}{VOL_PDF_PATH}{pdf}", "rb")
            readpdf = PyPDF2.PdfFileReader(pdf_file)
            total_pages = readpdf.numPages
            for image_counter in range(1, total_pages + 1):
                pdf_images_list.append(pdf.replace(".pdf", f"_{image_counter:04d}.jpg"))
        all_images = images_list + pdf_images_list
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as img_zip:
            # Iterate over all the files in directory
            for foldername, _, filenames in os.walk(f"{MEDIA_PATH}{IMG_PATH}"):
                for filename in filenames:
                    if filename in all_images:
                        # Create complete filepath of file in directory
                        filepath = os.path.join(foldername, filename)
                        # Add file to zip
                        img_zip.write(filepath, os.path.basename(filepath))
        response = HttpResponse(buffer.getvalue())
        response["Content-Type"] = "application/x-zip-compressed"
        response["Content-Disposition"] = "attachment; filename=images_volumes.zip"
        return response

    @admin.action(description="Exporter les documents PDF des Imprimés sélectionnés")
    def export_selected_pdfs(self, request, queryset):
        if len(queryset) > MAX_ITEMS:
            self.message_user(
                request,
                f"{MAX_ITEMS} éléments au maximum doivent être sélectionnés afin d'appliquer les actions.",
                messages.WARNING,
            )
            return HttpResponseRedirect(request.get_full_path())

        printed = queryset.exclude(volume__isnull=True)
        pdfs_list = printed.values_list("volume__pdfvolume__pdf", flat=True)
        pdfs_list = (pdf for pdf in pdfs_list if pdf is not None)
        pdfs_list = [f"{VHS_APP_URL}{settings.MEDIA_URL}{pdf}" for pdf in pdfs_list]

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as pdf_zip:
            for pdf_url in pdfs_list:
                pdf_name = os.path.basename(pdf_url)
                pdf_data = requests.get(pdf_url).content
                pdf_zip.writestr(pdf_name, pdf_data)

        response = HttpResponse(buffer.getvalue())
        response["Content-Type"] = "application/x-zip-compressed"
        response["Content-Disposition"] = "attachment; filename=pdfs_volumes.zip"
        return response

    @admin.action(
        description="Détecter la similarité entre les images des Imprimés sélectionnés"
    )
    def detect_similarity(self, request, queryset):
        host = env("GPU_REMOTE_HOST")
        username = env("GPU_USERNAME")
        password = env("GPU_PASSWORD")
        job_script_path = "SimilarityDetection/simdet.sh"
        remote_file_path = "SimilarityDetection/name_3.html"
        local_file_path = "vhsapp/templates/vhsapp/printed/output.html"
        ssh = connect_to_slurm_cluster(host, username, password)
        job_id = start_slurm_job(ssh, job_script_path)
        wait_for_job_completion(ssh, job_id)
        content = retrieve_result_file(ssh, remote_file_path, local_file_path)
        context = {"content": content}
        return render(request, "vhsapp/printed/template.html", context)

    @button(
        permission="demo.add_demomodel1",
        change_form=False,
        html_attrs={"style": "background-color:#88FF88;color:black"},
    )
    def exporter_images(self, request):
        url = "https://iscd.huma-num.fr/media/images_vhs.zip"
        return HttpResponseRedirect(url)


@admin.register(Volume)
class VolumeAdmin(admin.ModelAdmin):
    search_fields = ("title",)

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index
        """
        return {}


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_filter = ("name",)
    list_per_page = 5

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index
        """
        return {}


@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    search_fields = ("title",)
    list_filter = ("title",)
    list_per_page = 5

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index
        """
        return {}


@admin.register(DigitizedVersion)
class DigitizedVersionAdmin(admin.ModelAdmin):
    search_fields = ("source",)
    list_filter = ("source",)
    list_per_page = 5

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
        return format_html(
            '<a href="{}" target="_blank">{}</a>'.format(
                CANTALOUPE_APP_URL
                + "iiif/2/"
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


@admin.register(Manuscript)
class ManuscriptAdmin(ExtraButtonsMixin, admin.ModelAdmin):
    change_form_template = "admin/change.html"

    class Media:
        js = ("js/jquery-3.6.1.js", "js/script.js")

    list_display = (
        "short_author",
        "short_work",
        "conservation_place",
        "reference_number",
        "date_century",
        "sheets",
        "published",
    )
    ordering = ("id",)
    list_editable = ("date_century",)
    search_fields = ("author__name", "work__title")
    list_filter = (AuthorFilter, WorkFilter)
    autocomplete_fields = ("author", "work", "digitized_version")
    list_per_page = 100
    exclude = ("slug", "created_at", "updated_at")
    fieldsets = (
        (
            "Chaque manuscrit correspond à un exemplaire de l'oeuvre",
            {
                "fields": (
                    "manifest_auto",
                    "manifest_v2",
                    "manifest_final",
                    "author",
                    "work",
                    "conservation_place",
                    "reference_number",
                    "date_century",
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
    readonly_fields = ("manifest_auto", "manifest_v2")
    actions = [
        "export_selected_manifests",
        "export_selected_iiif_images",
        "export_selected_images",
        "export_selected_pdfs",
    ]
    inlines = [PdfManuscriptInline, ManifestManuscriptInline, ImageManuscriptInline]

    def manifest_auto(self, obj):
        url_manifest_auto = (
            f"{VHS_APP_URL}vhs/iiif/auto/manuscript/ms-{obj.id}/manifest.json"
        )
        link_manifest_auto = (
            '<a id="url_manifest_auto_'
            + str(obj.id)
            + '" href="/vhs/iiif/auto/manuscript/ms-'
            + str(obj.id)
            + '/manifest.json" target="_blank">'
            + url_manifest_auto
            + "</a> "
        )
        return mark_safe(
            link_manifest_auto
            + '<img alt="IIIF" src="https://iiif.io/assets/images/logos/logo-sm.png" height="15"/></a><br>'
            '<button id="annotate_manifest_auto_'
            + str(obj.id)
            + '" class="button" style="background-color:#EFB80B;color:white;padding:8px 10px;"><i class="fa-solid fa-eye"></i> VISUALISER ANNOTATIONS <i class="fa-solid fa-comment"></i></button><br>'
            '<a href="/vhs/iiif/auto/manuscript/'
            + str(obj.id)
            + '/annotation/" target="_blank"><i class="fa-solid fa-download"></i> Télécharger les annotations (CSV)</a>'
            '<span id="message_auto_' + str(obj.id) + '" style="color:#FF0000"></span>'
        )

    manifest_auto.short_description = "Manifeste (automatique)"

    def manifest_v2(self, obj):
        url_manifest = f"{VHS_APP_URL}vhs/iiif/v2/manuscript/ms-{obj.id}/manifest.json"
        link_manifest = (
            '<a id="url_manifest_'
            + str(obj.id)
            + '" href="/vhs/iiif/v2/manuscript/ms-'
            + str(obj.id)
            + '/manifest.json" target="_blank">'
            + url_manifest
            + "</a> "
        )
        if not obj.manifest_final:
            button = (
                '<button id="annotate_manifest_'
                + str(obj.id)
                + '" class="button" style="background-color:#008CBA;color:white;padding:8px 10px;"><i class="fa-solid fa-pen-to-square"></i> ÉDITER ANNOTATIONS <i class="fa-solid fa-comment"></i></button><br>'
            )
        else:
            button = (
                '<button id="manifest_final_'
                + str(obj.id)
                + '" class="button" style="background-color:#4CAF50;color:white;padding:8px 10px;"><i class="fa-solid fa-eye"></i> ANNOTATIONS FINALES <i class="fa-solid fa-comment"></i></button><br>'
            )
        return mark_safe(
            link_manifest
            + '<img alt="IIIF" src="https://iiif.io/assets/images/logos/logo-sm.png" height="15"/></a><br>'
            + button
            + '<a href="'
            + SAS_APP_URL
            + "search-api/ms-"
            + str(obj.id)
            + '/search" target="_blank"><i class="fa-solid fa-download"></i> Télécharger les annotations (JSON)</a>'
            '<span id="message_' + str(obj.id) + '" style="color:#FF0000"></span>'
        )

    manifest_v2.short_description = "Manifeste (en cours de vérification)"

    def get_fieldsets(self, request, obj=None):
        fieldsets = super(ManuscriptAdmin, self).get_fieldsets(request, obj)
        if not obj:
            from copy import deepcopy

            exclude_fieldsets = deepcopy(fieldsets)
            exclude_fieldsets[0][1]["fields"] = exclude_fieldsets[0][1]["fields"][3:]
            return exclude_fieldsets
        return fieldsets

    def short_author(self, obj):
        return truncatewords_html(obj.author, TRUNCATEWORDS)

    short_author.short_description = "Auteur"

    def short_work(self, obj):
        return truncatewords_html(obj.work, TRUNCATEWORDS)

    short_work.short_description = "Titre de l'oeuvre"

    def save_model(self, request, obj, form, change):
        if not obj.user:
            obj.user = request.user
        # Save the model instance
        obj.save()
        # Add a warning message
        messages.warning(
            request,
            "Le processus de conversion de.s fichier.s PDF en images et/ou d'extraction des images à partir de manifeste.s externe.s est en cours. Veuillez patienter quelques instants pour corriger les annotations automatiques.",
        )

        files = request.FILES.getlist("imagemanuscript_set-0-image")
        for file in files[:-1]:
            obj.imagemanuscript_set.create(image=file)

    @admin.action(description="Exporter les manifests IIIF des Manuscrits sélectionnés")
    def export_selected_manifests(self, request, queryset):
        manuscripts = queryset
        manifests_list = manuscripts.values_list("id", "manifestmanuscript__manifest")
        response = HttpResponse(content_type="text/csv")
        response[
            "Content-Disposition"
        ] = "attachment; filename=manifests_manuscripts.csv"
        writer = csv.writer(response)
        writer.writerow(["Manifest_IIIF"])
        for manifest in manifests_list:
            if mnf := manifest[1]:
                writer.writerow([mnf])
            else:
                writer.writerow(
                    [
                        f"{VHS_APP_URL}vhs/iiif/v2/manuscript/ms-{manifest[0]}/manifest.json"
                    ]
                )
        return response

    @admin.action(description="Exporter les images IIIF des Manuscrits sélectionnés")
    def export_selected_iiif_images(self, request, queryset):
        manuscripts = queryset
        images_list = manuscripts.values_list("imagemanuscript__image", flat=True)
        pdfs_list = manuscripts.values_list("pdfmanuscript__pdf", flat=True)
        images_list = [
            image.split("/")[-1] for image in images_list if image is not None
        ]
        pdfs_list = [pdf.split("/")[-1] for pdf in pdfs_list if pdf is not None]
        pdf_images_list = []
        for pdf in pdfs_list:
            pdf_file = open(f"{MEDIA_PATH}{MS_PDF_PATH}{pdf}", "rb")
            readpdf = PyPDF2.PdfFileReader(pdf_file)
            total_pages = readpdf.numPages
            for image_counter in range(1, total_pages + 1):
                pdf_images_list.append(pdf.replace(".pdf", f"_{image_counter:04d}.jpg"))
        all_images = images_list + pdf_images_list
        response = HttpResponse(content_type="text/csv")
        response[
            "Content-Disposition"
        ] = "attachment; filename=images_iiif_manuscripts.csv"
        writer = csv.writer(response)
        writer.writerow(["Image_IIIF"])
        for image in all_images:
            writer.writerow(
                [f"{CANTALOUPE_APP_URL}iiif/2/{image}/full/full/0/default.jpg"]
            )
        return response

    @admin.action(description="Exporter les images des Manuscrits sélectionnés")
    def export_selected_images(self, request, queryset):
        if len(queryset) > MAX_ITEMS:
            self.message_user(
                request,
                f"{MAX_ITEMS} éléments au maximum doivent être sélectionnés afin d'appliquer les actions.",
                messages.WARNING,
            )
            return HttpResponseRedirect(request.get_full_path())
        manuscripts = queryset
        images_list = manuscripts.values_list("imagemanuscript__image", flat=True)
        pdfs_list = manuscripts.values_list("pdfmanuscript__pdf", flat=True)
        images_list = [
            image.split("/")[-1] for image in images_list if image is not None
        ]
        pdfs_list = [pdf.split("/")[-1] for pdf in pdfs_list if pdf is not None]
        pdf_images_list = []
        for pdf in pdfs_list:
            pdf_file = open(f"{MEDIA_PATH}{MS_PDF_PATH}{pdf}", "rb")
            readpdf = PyPDF2.PdfFileReader(pdf_file)
            total_pages = readpdf.numPages
            for image_counter in range(1, total_pages + 1):
                pdf_images_list.append(pdf.replace(".pdf", f"_{image_counter:04d}.jpg"))
        all_images = images_list + pdf_images_list
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as img_zip:
            # Iterate over all the files in directory
            for foldername, _, filenames in os.walk(f"{MEDIA_PATH}{IMG_PATH}"):
                for filename in filenames:
                    if filename in all_images:
                        # Create complete filepath of file in directory
                        filepath = os.path.join(foldername, filename)
                        # Add file to zip
                        img_zip.write(filepath, os.path.basename(filepath))

        response = HttpResponse(buffer.getvalue())
        response["Content-Type"] = "application/x-zip-compressed"
        response["Content-Disposition"] = "attachment; filename=images_manuscripts.zip"
        return response

    @admin.action(description="Exporter les documents PDF des Manuscrits sélectionnés")
    def export_selected_pdfs(self, request, queryset):
        if len(queryset) > MAX_ITEMS:
            self.message_user(
                request,
                f"{MAX_ITEMS} éléments au maximum doivent être sélectionnés afin d'appliquer les actions.",
                messages.WARNING,
            )
            return HttpResponseRedirect(request.get_full_path())

        manuscripts = queryset.exclude(pdfmanuscript__pdf__isnull=True)
        pdfs_list = manuscripts.values_list("pdfmanuscript__pdf", flat=True)
        pdfs_list = [f"{VHS_APP_URL}{settings.MEDIA_URL}{pdf}" for pdf in pdfs_list]

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as pdf_zip:
            for pdf_url in pdfs_list:
                pdf_name = os.path.basename(pdf_url)
                pdf_data = requests.get(pdf_url).content
                pdf_zip.writestr(pdf_name, pdf_data)

        response = HttpResponse(buffer.getvalue())
        response["Content-Type"] = "application/x-zip-compressed"
        response["Content-Disposition"] = "attachment; filename=pdfs_manuscripts.zip"
        return response

    @button(
        permission="demo.add_demomodel1",
        change_form=False,
        html_attrs={"style": "background-color:#88FF88;color:black"},
    )
    def exporter_images(self, request):
        url = "https://iscd.huma-num.fr/media/images_vhs.zip"
        return HttpResponseRedirect(url)
