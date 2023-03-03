import zipfile

import nested_admin
from admin_extra_buttons.decorators import button
from admin_extra_buttons.mixins import ExtraButtonsMixin

from django.contrib import admin, messages
from django.http import HttpResponse, HttpResponseRedirect
from django.template.defaultfilters import truncatewords_html

from vhsapp.admin.admin import AuthorFilter, WorkFilter, DescriptiveElementsFilter

from vhsapp.models.witness import (
    Printed,
    Volume,
    Manuscript,
)

from vhsapp.models.constants import MS, VOL

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
from vhsapp.utils.paths import (
    MEDIA_PATH,
    VOL_PDF_PATH,
    IMG_PATH,
    MS_PDF_PATH,
)

from vhsapp.utils.iiif import get_link_manifest, gen_btn, gen_manifest_url, gen_img_url
from vhsapp.utils.functions import list_to_csv, zip_img, get_file_list


class WitnessAdmin(ExtraButtonsMixin, admin.ModelAdmin):
    class Meta:
        verbose_name = "Witness"
        verbose_name_plural = "Witnesses"
        abstract = True

    ordering = ("id",)
    list_filter = (AuthorFilter, WorkFilter)
    autocomplete_fields = ("author", "work")
    list_per_page = 100
    exclude = ("slug", "created_at", "updated_at")
    readonly_fields = ("manifest_auto", "manifest_v2")
    actions = [
        "export_selected_manifests",
        "export_selected_iiif_images",
        "export_selected_images",
        "export_selected_pdfs",
    ]

    def check_selection(self, queryset, request):
        if len(queryset) > MAX_ITEMS:
            self.message_user(
                request,
                f"Actions can be performed on up to {MAX_ITEMS} elements only.",
                messages.WARNING,
            )
            return True
        return False

    def manifest_auto(self, obj):
        # if manifest_first := obj.manifestmanuscript_set.first():
        #     return mark_safe(f"{get_link_manifest(obj.id, manifest_first)}<br>")
        return gen_btn(obj.id, "VISUALIZE", MANIFEST_AUTO, MS.lower())

    manifest_auto.short_description = "Manifeste (automatique)"

    def manifest_v2(self, obj):
        return gen_btn(
            obj.id, "FINAL" if obj.manifest_final else "EDIT", MANIFEST_V2, MS.lower()
        )

    manifest_v2.short_description = "Manifeste (en cours de vérification)"

    def short_author(self, obj):
        return truncatewords_html(obj.author, TRUNCATEWORDS)

    short_author.short_description = "Auteur"

    def short_work(self, obj):
        return truncatewords_html(obj.work, TRUNCATEWORDS)

    short_work.short_description = "Titre de l'oeuvre"

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

        files = request.FILES.getlist("imagemanuscript_set-0-image")
        for file in files[:-1]:
            obj.imagemanuscript_set.create(image=file)

    @admin.action(description="Exporter les manifests IIIF des Manuscrits sélectionnés")
    def export_selected_manifests(self, request, queryset):
        results = queryset.exclude(volume__isnull=True).values_list("volume__id")
        manifests = [
            gen_manifest_url(
                mnf[0], request.scheme, request.META["HTTP_HOST"], None, MANIFEST_V2
            )
            for mnf in results
        ]
        return list_to_csv(manifests, "Manifest_IIIF")

    @admin.action(description="Exporter les images IIIF des Manuscrits sélectionnés")
    def export_selected_iiif_images(self, request, queryset):
        img_list = [
            gen_img_url(img, request.scheme, request.META["HTTP_HOST"])
            for img in self.get_img_list(queryset)
        ]
        return list_to_csv(img_list, "Image_IIIF")

    @admin.action(description="Exporter les images des Manuscrits sélectionnés")
    def export_selected_images(self, request, queryset):
        if self.check_selection(queryset, request):
            return HttpResponseRedirect(request.get_full_path())
        return zip_img(zipfile, get_file_list(IMG_PATH, self.get_img_list(queryset)))

    @admin.action(description="Exporter les documents PDF des Manuscrits sélectionnés")
    def export_selected_pdfs(self, request, queryset):
        if self.check_selection(queryset, request):
            return HttpResponseRedirect(request.get_full_path())
        return zip_img(
            zipfile, self.get_img_list(queryset, with_img=False, with_pdf=True), "pdf"
        )

    @button(
        permission="demo.add_demomodel1",
        change_form=False,
        html_attrs={"style": "background-color:#88FF88;color:black"},
    )
    def exporter_images(self, request):
        url = "https://iscd.huma-num.fr/media/images_vhs.zip"  # TODO CHANGE THAT
        return HttpResponseRedirect(url)


@admin.register(Manuscript)
class ManuscriptAdmin(WitnessAdmin):
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
    search_fields = ("author__name", "work__title")
    autocomplete_fields = ("author", "work", "digitized_version")
    list_editable = ("date_century",)
    inlines = [PdfManuscriptInline, ManifestManuscriptInline, ImageManuscriptInline]
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

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        files = request.FILES.getlist("imagemanuscript_set-0-image")
        for file in files[:-1]:
            obj.imagemanuscript_set.create(image=file)

    # @admin.action(description="Exporter les manifests IIIF des Manuscrits sélectionnés")
    # def export_selected_manifests(self, request, queryset):
    #     results = queryset.exclude(volume__isnull=True).values_list("volume__id")
    #     manifests = [
    #         gen_manifest_url(
    #             mnf[0], request.scheme, request.META["HTTP_HOST"], None, MANIFEST_V2
    #         )
    #         for mnf in results
    #     ]
    #     return list_to_csv(manifests, "Manifest_IIIF")
    #     # manuscripts = queryset
    #     # manifests_list = manuscripts.values_list("id", "manifestmanuscript__manifest")
    #     # response = HttpResponse(content_type="text/csv")
    #     # response[
    #     #     "Content-Disposition"
    #     # ] = "attachment; filename=manifests_manuscripts.csv"
    #     # writer = csv.writer(response)
    #     # writer.writerow(["Manifest_IIIF"])
    #     # for manifest in manifests_list:
    #     #     if mnf := manifest[1]:
    #     #         writer.writerow([mnf])
    #     #     else:
    #     #         writer.writerow(
    #     #             [
    #     #                 request.scheme
    #     #                 + "://"
    #     #                 + request.META["HTTP_HOST"]
    #     #                 + "/vhs/iiif/v2/manuscript/ms-"
    #     #                 + str(manifest[0])
    #     #                 + "/manifest.json"
    #     #             ]
    #     #         )
    #     # return response

    # @admin.action(description="Exporter les images IIIF des Manuscrits sélectionnés")
    # def export_selected_iiif_images(self, request, queryset):
    #     img_list = [
    #         gen_img_url(img, request.scheme, request.META["HTTP_HOST"])
    #         for img in self.get_img_list(queryset)
    #     ]
    #     return list_to_csv(img_list, "Image_IIIF")
    #     # manuscripts = queryset
    #     # images_list = manuscripts.values_list("imagemanuscript__image", flat=True)
    #     # pdfs_list = manuscripts.values_list("pdfmanuscript__pdf", flat=True)
    #     # images_list = [
    #     #     image.split("/")[-1] for image in images_list if image is not None
    #     # ]
    #     # pdfs_list = [pdf.split("/")[-1] for pdf in pdfs_list if pdf is not None]
    #     # pdf_images_list = []
    #     # for pdf in pdfs_list:
    #     #     pdf_file = open(f"{MEDIA_PATH}{MS_PDF_PATH}{pdf}", "rb")
    #     #     readpdf = PyPDF2.PdfFileReader(pdf_file)
    #     #     total_pages = readpdf.numPages
    #     #     for image_counter in range(1, total_pages + 1):
    #     #         pdf_images_list.append(
    #     #             pdf.replace(".pdf", "_{:04d}".format(image_counter) + ".jpg")
    #     #         )
    #     # all_images = images_list + pdf_images_list
    #     # response = HttpResponse(content_type="text/csv")
    #     # response[
    #     #     "Content-Disposition"
    #     # ] = "attachment; filename=images_iiif_manuscripts.csv"
    #     # writer = csv.writer(response)
    #     # writer.writerow(["Image_IIIF"])
    #     # for image in all_images:
    #     #     writer.writerow(
    #     #         [
    #     #             request.scheme
    #     #             + "://"
    #     #             + request.META["HTTP_HOST"]
    #     #             + "/iiif/2/"
    #     #             + image
    #     #             + "/full/full/0/default.jpg"
    #     #         ]
    #     #     )
    #     # return response

    # @admin.action(description="Exporter les images des Manuscrits sélectionnés")
    # def export_selected_images(self, request, queryset):
    #     if self.check_selection(queryset, request):
    #         return HttpResponseRedirect(request.get_full_path())
    #     return zip_img(zipfile, get_file_list(IMG_PATH, self.get_img_list(queryset)))
    #
    #     # manuscripts = queryset
    #     # images_list = manuscripts.values_list("imagemanuscript__image", flat=True)
    #     # pdfs_list = manuscripts.values_list("pdfmanuscript__pdf", flat=True)
    #     # images_list = [
    #     #     image.split("/")[-1] for image in images_list if image is not None
    #     # ]
    #     # pdfs_list = [pdf.split("/")[-1] for pdf in pdfs_list if pdf is not None]
    #     # pdf_images_list = []
    #     # for pdf in pdfs_list:
    #     #     pdf_file = open(f"{MEDIA_PATH}{MS_PDF_PATH}{pdf}", "rb")
    #     #     readpdf = PyPDF2.PdfFileReader(pdf_file)
    #     #     total_pages = readpdf.numPages
    #     #     for image_counter in range(1, total_pages + 1):
    #     #         pdf_images_list.append(
    #     #             pdf.replace(".pdf", "_{:04d}".format(image_counter) + ".jpg")
    #     #         )
    #     # all_images = images_list + pdf_images_list
    #     # buffer = io.BytesIO()
    #     # with zipfile.ZipFile(buffer, "w") as img_zip:
    #     #     # Iterate over all the files in directory
    #     #     for foldername, _, filenames in os.walk(f"{MEDIA_PATH}{IMG_PATH}"):
    #     #         for filename in filenames:
    #     #             if filename in all_images:
    #     #                 # Create complete filepath of file in directory
    #     #                 filepath = os.path.join(foldername, filename)
    #     #                 # Add file to zip
    #     #                 img_zip.write(filepath, os.path.basename(filepath))
    #     #
    #     # response = HttpResponse(buffer.getvalue())
    #     # response["Content-Type"] = "application/x-zip-compressed"
    #     # response["Content-Disposition"] = "attachment; filename=images_manuscripts.zip"
    #     # return response

    # @admin.action(description="Exporter les documents PDF des Manuscrits sélectionnés")
    # def export_selected_pdfs(self, request, queryset):
    #     if self.check_selection(queryset, request):
    #         return HttpResponseRedirect(request.get_full_path())
    #     return zip_img(
    #         zipfile, self.get_img_list(queryset, with_img=False, with_pdf=True), "pdf"
    #     )
    #
    #     # manuscripts = queryset.exclude(pdfmanuscript__pdf__isnull=True)
    #     # pdfs_list = manuscripts.values_list("pdfmanuscript__pdf", flat=True)
    #     # pdfs_list = [
    #     #     request.scheme
    #     #     + "://"
    #     #     + request.META["HTTP_HOST"]
    #     #     + "/"
    #     #     + settings.MEDIA_URL
    #     #     + s
    #     #     for s in pdfs_list
    #     # ]
    #     #
    #     # buffer = io.BytesIO()
    #     # with zipfile.ZipFile(buffer, "w") as pdf_zip:
    #     #     for pdf_url in pdfs_list:
    #     #         pdf_name = os.path.basename(pdf_url)
    #     #         pdf_data = requests.get(pdf_url).content
    #     #         pdf_zip.writestr(pdf_name, pdf_data)
    #     #
    #     # response = HttpResponse(buffer.getvalue())
    #     # response["Content-Type"] = "application/x-zip-compressed"
    #     # response["Content-Disposition"] = "attachment; filename=pdfs_manuscripts.zip"
    #     # return response

    # @button(
    #     permission="demo.add_demomodel1",
    #     change_form=False,
    #     html_attrs={"style": "background-color:#88FF88;color:black"},
    # )
    # def exporter_images(self, request):
    #     url = "https://iscd.huma-num.fr/media/images_vhs.zip"  # TODO CHANGE THAT
    #     return HttpResponseRedirect(url)


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
            # if manifest_first := obj.manifestvolume_set.first():
            #     return mark_safe(f"{get_link_manifest(obj.id, manifest_first)}<br>")
            return gen_btn(obj.id)
        return "-"

    manifest_auto.short_description = "Manifeste (automatique)"

    def manifest_v2(self, obj):
        if obj.id:
            return gen_btn(
                obj.id, "FINAL" if obj.manifest_final else "EDIT", MANIFEST_V2
            )
        return "-"

    manifest_v2.short_description = "Manifeste (en cours de vérification)"

    def get_fields(self, request, obj=None):
        """ """
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
    ]
    inlines = [VolumeInline]

    def check_selection(self, queryset, request):
        if len(queryset) > MAX_ITEMS:
            self.message_user(
                request,
                f"Actions can be performed on up to {MAX_ITEMS} elements only.",
                messages.WARNING,
            )
            return True
        return False

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
        results = queryset.exclude(volume__isnull=True).values_list("volume__id")
        manifests = [
            gen_manifest_url(
                mnf[0], request.scheme, request.META["HTTP_HOST"], None, MANIFEST_V2
            )
            for mnf in results
        ]
        return list_to_csv(manifests, "Manifest_IIIF")
        # printed = queryset.exclude(volume__isnull=True)
        # manifests_list = printed.values_list(
        #     "volume__id", "volume__manifestvolume__manifest"
        # )
        # response = HttpResponse(content_type="text/csv")
        # response["Content-Disposition"] = "attachment; filename=manifests_volumes.csv"
        # writer = csv.writer(response)
        # writer.writerow(["Manifest_IIIF"])
        # for manifest in manifests_list:
        #     if mnf := manifest[1]:
        #         writer.writerow([mnf])
        #     else:
        #         writer.writerow(
        #             [
        #                 request.scheme
        #                 + "://"
        #                 + request.META["HTTP_HOST"]
        #                 + "/vhs/iiif/v2/volume/vol-"
        #                 + str(manifest[0])
        #                 + "/manifest.json"
        #             ]
        #         )
        # return response

    @admin.action(description="Exporter les images IIIF des Imprimés sélectionnés")
    def export_selected_iiif_images(self, request, queryset):
        img_list = [
            gen_img_url(img, request.scheme, request.META["HTTP_HOST"])
            for img in self.get_img_list(queryset)
        ]
        return list_to_csv(img_list, "Image_IIIF")
        # printed = queryset.exclude(volume__isnull=True)
        # images_list = printed.values_list("volume__imagevolume__image", flat=True)
        # pdfs_list = printed.values_list("volume__pdfvolume__pdf", flat=True)
        # images_list = [
        #     image.split("/")[-1] for image in images_list if image is not None
        # ]
        # pdfs_list = [pdf.split("/")[-1] for pdf in pdfs_list if pdf is not None]
        # pdf_images_list = []
        # for pdf in pdfs_list:
        #     pdf_file = Pdf.open(f"{MEDIA_PATH}{VOL_PDF_PATH}{pdf}")
        #     total_pages = len(pdf_file.pages)
        #     for image_counter in range(1, total_pages + 1):
        #         pdf_images_list.append(
        #             pdf.replace(".pdf", "_{:04d}".format(image_counter) + ".jpg")
        #         )
        # all_images = images_list + pdf_images_list
        # response = HttpResponse(content_type="text/csv")
        # response["Content-Disposition"] = "attachment; filename=images_iiif_volumes.csv"
        # writer = csv.writer(response)
        # writer.writerow(["Image_IIIF"])
        # for image in all_images:
        #     writer.writerow(
        #         [
        #             request.scheme
        #             + "://"
        #             + request.META["HTTP_HOST"]
        #             + "/iiif/2/"
        #             + image
        #             + "/full/full/0/default.jpg"
        #         ]
        #     )
        # return response

    @admin.action(description="Exporter les images des Imprimés sélectionnés")
    def export_selected_images(self, request, queryset):
        if self.check_selection(queryset, request):
            return HttpResponseRedirect(request.get_full_path())
        return zip_img(zipfile, get_file_list(IMG_PATH, self.get_img_list(queryset)))
        # printed = queryset.exclude(volume__isnull=True)
        # images_list = printed.values_list("volume__imagevolume__image", flat=True)
        # pdfs_list = printed.values_list("volume__pdfvolume__pdf", flat=True)
        # images_list = [
        #     image.split("/")[-1] for image in images_list if image is not None
        # ]
        # pdfs_list = [pdf.split("/")[-1] for pdf in pdfs_list if pdf is not None]
        # pdf_images_list = []
        # for pdf in pdfs_list:
        #     pdf_file = open(f"{MEDIA_PATH}{VOL_PDF_PATH}{pdf}", "rb")
        #     readpdf = PyPDF2.PdfFileReader(pdf_file)
        #     total_pages = readpdf.numPages
        #     for image_counter in range(1, total_pages + 1):
        #         pdf_images_list.append(
        #             pdf.replace(".pdf", "_{:04d}".format(image_counter) + ".jpg")
        #         )
        # all_images = images_list + pdf_images_list
        # buffer = io.BytesIO()
        # with zipfile.ZipFile(buffer, "w") as img_zip:
        #     # Iterate over all the files in directory
        #     for foldername, _, filenames in os.walk(f"{MEDIA_PATH}{IMG_PATH}"):
        #         for filename in filenames:
        #             if filename in all_images:
        #                 # Create complete filepath of file in directory
        #                 filepath = os.path.join(foldername, filename)
        #                 # Add file to zip
        #                 img_zip.write(filepath, os.path.basename(filepath))
        # response = HttpResponse(buffer.getvalue())
        # response["Content-Type"] = "application/x-zip-compressed"
        # response["Content-Disposition"] = "attachment; filename=images_volumes.zip"
        # return response

    @admin.action(description="Exporter les documents PDF des Imprimés sélectionnés")
    def export_selected_pdfs(self, request, queryset):
        if self.check_selection(queryset, request):
            return HttpResponseRedirect(request.get_full_path())
        return zip_img(
            zipfile, self.get_img_list(queryset, with_img=False, with_pdf=True), "pdf"
        )
        # printed = queryset.exclude(volume__isnull=True)
        # pdfs_list = printed.values_list("volume__pdfvolume__pdf", flat=True)
        # pdfs_list = (pdf for pdf in pdfs_list if pdf is not None)
        # pdfs_list = [
        #     request.scheme
        #     + "://"
        #     + request.META["HTTP_HOST"]
        #     + "/"
        #     + settings.MEDIA_URL
        #     + s
        #     for s in pdfs_list
        # ]
        #
        # buffer = io.BytesIO()
        # with zipfile.ZipFile(buffer, "w") as pdf_zip:
        #     for pdf_url in pdfs_list:
        #         pdf_name = os.path.basename(pdf_url)
        #         pdf_data = requests.get(pdf_url).content
        #         pdf_zip.writestr(pdf_name, pdf_data)
        #
        # response = HttpResponse(buffer.getvalue())
        # response["Content-Type"] = "application/x-zip-compressed"
        # response["Content-Disposition"] = "attachment; filename=pdfs_volumes.zip"
        # return response

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
