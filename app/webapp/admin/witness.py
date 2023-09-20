from app.config.settings import APP_LANG
from app.webapp.admin import DigitizationInline, ContentInline, ContentWorkInline
from app.webapp.models import MS_ABBR, MS, VOL
from app.webapp.models.witness import Witness, get_name
from app.webapp.utils.constants import (
    MANIFEST_V1,
    MANIFEST_V2,
    MAX_ITEMS,
    TRUNCATEWORDS,
)

import nested_admin
from admin_extra_buttons.mixins import ExtraButtonsMixin

from django.contrib import admin, messages
from django.utils.safestring import mark_safe

from app.webapp.utils.iiif import gen_iiif_url
from app.webapp.utils.functions import list_to_txt, zip_img


# TODO change MS/VOL


def get_img_prefix(obj: Witness, wit_abbr=MS_ABBR):
    # TODO find a solution that better suits the new app structure and data model
    return f"{wit_abbr}{obj.id}"


@admin.register(Witness)
class WitnessAdmin(ExtraButtonsMixin, nested_admin.NestedModelAdmin):
    # DEFINITION OF THE MAIN FORM => Add Witness
    class Media:
        css = {"all": ("css/form.css",)}
        js = ("js/witness-form.js",)

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.actions = [
            "export_selected_manifests",
            "export_selected_iiif_images",
            "export_selected_images",
            # TODO add export annotations as training data
        ]

    ordering = ("id", "place__name")
    list_per_page = 100

    # Fields that are taken into account by the search bar
    search_fields = (
        "id_nb",
        "place__name",
        "type",
        "contents__roles__person__name",  # todo check if it works
        "contents__work__name",
    )
    # Filters options in the sidebar
    list_filter = ("id_nb", "place")  # list_filter = (AuthorFilter, WorkFilter)
    # Attributes to be excluded from the form fields
    exclude = ("slug", "created_at", "updated_at")
    # Dropdown fields
    autocomplete_fields = ("place", "volume")

    # MARKER FORM FIELDS
    # info on fieldsets: https://docs.djangoproject.com/en/4.2/ref/contrib/admin/#django.contrib.admin.ModelAdmin.fieldsets
    banner = (
        f"{get_name('Witness')} identification"
        if APP_LANG == "en"
        else f"Identification du {get_name('Witness')}"
    )
    fieldsets = (
        (
            banner.capitalize(),
            {
                "fields": [
                    "type",
                    ("id_nb", "place"),  # place and id_nb appear on the same line
                    ("page_type", "nb_pages"),  # same
                    "notes",
                    ("title", "volume"),
                    "is_public",
                ]
            },
        ),
    )

    # MARKER SUB-FORMS existing within the Witness form
    inlines = [DigitizationInline, ContentInline]

    def get_inline_instances(self, request, obj=None):
        # TODO finish this
        # called every time the form is rendered without need of refreshing the page
        inline_instances = super().get_inline_instances(request, obj)

        # Exclude Volume if the type is "manuscript"
        # if obj and obj.type == "manuscript":
        #     inline_instances = [
        #         inline
        #         for inline in inline_instances
        #         if not isinstance(inline, VolumeInline)
        #     ]

        return inline_instances

    # MARKER ADDITIONAL FIELDS

    # TODO add a field to access to direct annotation int the list view

    # MARKER SAVING METHODS

    def save_file(self, request, obj):
        # instantiated by inheritance (following code is fake) TODO check utility
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
            "les annotations automatiques.",  # TODO bilingual
        )
        self.save_file(request, obj)

    # # # # # # # # # # # #
    # MARKER WITNESS LIST #
    # # # # # # # # # # # #

    # MARKER LIST COLUMNS
    @admin.display(description="Annotation")
    def is_annotated(self, obj: Witness):
        # To display a button in the list of witnesses to know if they were annotated or not
        return mark_safe("<br>".join(digit.anno_btn() for digit in obj.get_digits()))

    @admin.display(description="IIIF manifest")
    def manifest_link(self, obj):
        # To display a button in the list of witnesses to give direct link to witness manifest
        return mark_safe(
            "<br>".join(digit.manifest_link() for digit in obj.get_digits())
        )

    @admin.display(
        description=get_name("Person", plural=True),
        # ordering= TODO find something to order the column
    )
    def authors(self, obj: Witness):
        return obj.get_person_names()

    # # or TODO authors.admin_order_field = (
    #     "-author__name"  # By what value to order this column in the admin list view
    # )

    # list of fields that are displayed in the witnesses list view
    list_display = (
        "id",
        "id_nb",
        "place",
        "authors",
        "manifest_link",
        "is_annotated",
    )
    list_display_links = ("id_nb",)

    # MARKER LIST ACTIONS

    def get_img_list(self, queryset, with_img=True, with_pdf=True):
        results = queryset.exclude()
        result_list = []
        # TODO redo this method, probably by creating a Witness method to retrieve witness images
        # wit_type = self.wit_type()
        #
        # if with_img:
        #     field_tag = (
        #         f"{wit_type}__image{wit_type}__image"
        #         if wit_type == VOL.lower()
        #         else f"image{wit_type}__image"
        #     )
        #     img_list = results.values_list(field_tag, flat=True)
        #     img_list = [img.split("/")[-1] for img in img_list if img is not None]
        #     result_list = result_list + img_list
        #
        # if with_pdf:
        #     field_tag = (
        #         f"{wit_type}__pdf{wit_type}__pdf"
        #         if wit_type == VOL.lower()
        #         else f"pdf{wit_type}__pdf"
        #     )
        #     pdf_list = results.values_list(field_tag, flat=True)
        #     pdf_list = [pdf.split("/")[-1] for pdf in pdf_list if pdf is not None]
        #     result_list = result_list + get_pdf_imgs(pdf_list, wit_type)

        return result_list

    @admin.action(
        description="Exporter les images IIIF sélectionnées"
    )  # TODO bilingual
    def export_selected_iiif_images(self, request, queryset):
        img_list = [gen_iiif_url(img) for img in self.get_img_list(queryset)]
        return list_to_txt(img_list, f"IIIF_images")

    def check_selection(self, queryset, request):
        if len(queryset) > MAX_ITEMS:
            self.message_user(
                request,
                f"Actions can be performed on up to {MAX_ITEMS} elements only.",
                messages.WARNING,
            )
            return True
        return False

    # @admin.action(description="Exporter les images sélectionnées")
    # def export_selected_images(self, request, queryset):
    #     if self.check_selection(queryset, request):
    #         return HttpResponseRedirect(request.get_full_path())
    #     # NOTE get_file_list(IMG_PATH, self.get_img_list(queryset)) is returning None
    #     return zip_img(zipfile, get_file_list(IMG_PATH, self.get_img_list(queryset)))

    @admin.action(
        description="Exporter les manifests IIIF sélectionnés"
    )  # TODO bilingual
    def export_selected_manifests(self, request, queryset):
        # results = queryset.exclude(volume__isnull=True).values_list("volume__id")
        results = queryset.values_list(  # TODO : here change for digit
            "id", "manifestmanuscript__manifest"
        )
        manifests = [digit.gen_manifest_url() for digit in results]
        return list_to_txt(manifests, "Manifest_IIIF")

    @admin.action(description="Export diagram images in selected sources")
    def export_annotated_imgs(self, request, queryset):
        if queryset.count() > 5:
            messages.warning(request, "You can select up to 5 manuscripts for export.")
            return

        results = queryset.values_list("id")

        img_urls = []
        for wit_id in results:
            witness = Witness.objects.get(pk=wit_id[0])
            # img_urls.extend(get_anno_images(anno)) TODO : here change for anno

        return zip_img(request, img_urls)


class WitnessInline(nested_admin.NestedStackedInline):
    # FORM contained in the Series form
    model = Witness
    verbose_name_plural = ""  # No title in the blue banner on top of the inline form
    extra = 1
    # classes = ("collapse",)
    fields = [("id_nb", "place"), "volume"]
    inlines = [ContentWorkInline]
    autocomplete_fields = ("place", "volume")
