from app.config.settings import APP_LANG
from app.webapp.admin import DigitizationInline, VolumeInline
from app.webapp.models import MS_ABBR, MS, VOL
from app.webapp.models.witness import Witness, get_name
from app.webapp.utils.constants import (
    MANIFEST_AUTO,
    MANIFEST_V2,
    MAX_ITEMS,
    TRUNCATEWORDS,
)

import nested_admin
from admin_extra_buttons.decorators import button
from admin_extra_buttons.mixins import ExtraButtonsMixin

from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.template.defaultfilters import truncatewords_html
from django.utils.safestring import mark_safe

from app.webapp.utils.iiif import gen_iiif_url
from app.webapp.utils.iiif.annotation import has_annotations
from app.webapp.utils.iiif.manifest import has_manifest, gen_manifest_url
from app.webapp.utils.iiif.gen_html import gen_btn, gen_manifest_btn
from app.webapp.utils.functions import list_to_txt, get_pdf_imgs, anno_btn


# TODO change MS/VOL


def get_img_prefix(obj: Witness, wit_abbr=MS_ABBR):
    # TODO find a solution that better suits the new app structure and data model
    return f"{wit_abbr}{obj.id}"


@admin.register(Witness)
class WitnessAdmin(ExtraButtonsMixin, admin.ModelAdmin):
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
        "contents__roles__person__name",
        "contents__work__name",
    )
    # Filters options in the sidebar
    list_filter = ("id_nb", "place")  # list_filter = (AuthorFilter, WorkFilter)
    # Attributes to be excluded from the form fields
    exclude = ("slug", "created_at", "updated_at")
    # Dropdown fields
    autocomplete_fields = ("place",)
    # Fields that cannot be modified by the User
    readonly_fields = ("manifest_auto", "manifest_v2")

    # MARKER FORM FIELDS
    # info on fieldsets: https://docs.djangoproject.com/en/4.2/ref/contrib/admin/#django.contrib.admin.ModelAdmin.fieldsets
    fieldsets = (
        (
            None,  # Text to be displayed in the banner on top of this part of the form
            {
                "fields": [
                    "type",
                    ("id_nb", "place"),  # place and id_nb appear on the same line
                ]
            },
        ),
        """
        ( # fields to be displayed only for prints (i.e. "wpr" and "tpr")
            "Print description" if APP_LANG == "en" else "Description de l'imprimé",
            {
                "fields": ("title",),
                "classes": ("print-field",),
            },
        ),
        """,
        (  # fields to be displayed only for prints (i.e. "wpr" and "tpr")
            get_name("Digitization"),
            {
                "fields": ("title",),
                "classes": ("print-field",),
            },
        ),
    )

    # def get_fieldsets(self, request, obj: Witness = None):
    #     # called every time the form is rendered without need of refreshing the page
    #     fieldsets = super().get_fieldsets(request, obj=obj)
    #
    #     # TODO: exclude manifest fields when no digitization was uploaded
    #
    #     if obj:
    #         # when the witness is a print (i.e. "wpr" and "tpr"), display all the fields
    #         if obj.type != "manuscript":
    #             return fieldsets
    #
    #         # from copy import deepcopy
    #         # exclude_fieldsets = deepcopy(fieldsets)
    #         # exclude_fieldsets[0][1]["fields"] = exclude_fieldsets[0][1]["fields"][3:]
    #
    #         # else, exclude "title" TODO finish to remove "title"
    #         fieldsets[0][1]["fields"] = tuple(
    #             field for field in fieldsets[0][1]["fields"] if field != "title"
    #         )
    #
    #     return fieldsets

    # MARKER SUB-FORMS existing within the Witness form
    inlines = [DigitizationInline, VolumeInline]

    def get_inline_instances(self, request, obj=None):
        # TODO finish this
        # called every time the form is rendered without need of refreshing the page
        inline_instances = super().get_inline_instances(request, obj)

        # Exclude Volume if the type is "manuscript"
        if obj and obj.type == "manuscript":
            inline_instances = [
                inline
                for inline in inline_instances
                if not isinstance(inline, VolumeInline)
            ]

        return inline_instances

    # MARKER ADDITIONAL FIELDS

    def manifest_auto(self, obj, wit_abbr=MS_ABBR):
        if obj.id:
            img_prefix = get_img_prefix(obj, wit_abbr)
            action = "view" if has_manifest(img_prefix) else "no_manifest"
            return gen_btn(obj.id, action, MANIFEST_AUTO, self.wit_name().lower())
        return "-"

    manifest_auto.short_description = "Manifeste (automatique)"  # TODO bilingual

    def manifest_v2(self, obj, wit_type=MS_ABBR):
        if obj.id:
            action = "final" if obj.manifest_final else "edit"
            if not has_annotations(obj, wit_type):
                action = "no_anno"
            return gen_btn(obj.id, action, MANIFEST_V2, self.wit_name().lower())
        return "-"

    manifest_v2.short_description = "Manifeste (modifiable)"  # TODO bilingual

    # MARKER SAVING METHODS

    def save_file(self, request, obj):
        # instantiated by inheritance (following code is fake) TODO check utilitu
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
    def is_annotated(self, obj: Witness, wit_abbr=MS_ABBR):
        # To display a button in the list of witnesses to know if they were annotated or not
        action = "final" if obj.is_validated else "edit"
        return mark_safe(
            anno_btn(
                obj.id,
                action if has_annotations(obj, wit_abbr) else "no_anno",
            )
        )

    is_annotated.short_description = "Annotation"

    def manifest_link(self, obj, wit_abbr=MS_ABBR):
        # To display a button in the list of witnesses to give direct link to witness manifest
        wit_type = MS if wit_abbr == MS_ABBR else VOL
        return gen_manifest_btn(
            obj.id, wit_type, has_manifest(get_img_prefix(obj, wit_abbr))
        )

    manifest_link.short_description = "IIIF manifest"

    # TODO authors method to access all authors
    def authors(self, obj: Witness):
        return obj.get_persons()

    authors.short_description = "persons"  # TODO bilingual and with use of constants

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
        results = queryset.values_list(
            "id", "manifestmanuscript__manifest"
        )  # TODO make it available for all witnesses
        manifests = [
            gen_manifest_url(mnf[0], MANIFEST_V2, MS.lower()) for mnf in results
        ]
        return list_to_txt(manifests, "Manifest_IIIF")


class WitnessInline(nested_admin.NestedStackedInline):
    # FORM to be contained within the Series form
    model = Witness

    # TODO CHANGE FROM THIS TO END OF CLASS
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
    autocomplete_fields = ("",)
    extra = 0
    classes = ("collapse",)
    inlines = [DigitizationInline]

    def wit_name(self):
        return VOL

    def get_fields(self, request, obj=None):
        fields = list(super(WitnessInline, self).get_fields(request, obj))
        exclude_set = set()
        if not obj:  # obj will be None on the add page, and something on change pages
            exclude_set.add("manifest_auto")
            exclude_set.add("manifest_v2")
            exclude_set.add("manifest_final")
        return [f for f in fields if f not in exclude_set]

    # # TODO use Abstract Model ManifestAdmin instead
    # readonly_fields = ("manifest_auto", "manifest_v2")
    #
    # def manifest_auto(self, obj):
    #     if obj.id:
    #         img_prefix = get_img_prefix(obj, VOL_ABBR)
    #         action = "view" if has_manifest(img_prefix) else "no_manifest"
    #         return gen_btn(obj.id, action, MANIFEST_AUTO, self.wit_name().lower())
    #     return "-"
    #
    # manifest_auto.short_description = "Manifeste (automatique)"
    #
    # def manifest_v2(self, obj):
    #     if obj.id:
    #         action = "final" if obj.manifest_final else "edit"
    #         if not has_annotations(obj, VOL_ABBR):
    #             action = "no_anno"
    #         return gen_btn(obj.id, action, MANIFEST_V2, self.wit_name().lower())
    #     return "-"
    #
    # manifest_v2.short_description = "Manifeste (modifiable)"
