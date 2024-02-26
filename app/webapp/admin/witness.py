from app.config.settings import APP_LANG
from app.webapp.admin.digitization import DigitizationInline
from app.webapp.admin.content import ContentInline, ContentWorkInline

# from app.webapp.admin.volume import VolumeInline
from app.webapp.models.utils.constants import WIT, ANNO, DIG
from app.webapp.models.witness import Witness, get_name
from app.webapp.utils.constants import MAX_ITEMS

import nested_admin
from admin_extra_buttons.mixins import ExtraButtonsMixin

from django.contrib import admin, messages
from django.utils.safestring import mark_safe

from app.webapp.utils.iiif import gen_iiif_url
from app.webapp.utils.functions import (
    list_to_txt,
    zip_img,
    get_file_ext,
    zip_dirs,
    format_dates,
)
from app.webapp.utils.iiif.annotation import get_anno_images, get_training_anno
from app.webapp.utils.paths import IMG_PATH


def no_anno_message(request):
    messages.warning(
        request,
        f"Please select at least one {WIT} with annotations."
        if APP_LANG == "en"
        else f"Merci de sélectionner au moins un {WIT} avec des annotations.",
    )


def check_selection(queryset, request):
    if len(queryset) > MAX_ITEMS:
        messages.warning(
            request,
            f"You can select up to 5 {WIT}es."
            if APP_LANG == "en"
            else f"Vous pouvez sélectionner jusqu'à 5 {WIT}s.",
        )
        return False
    return True


@admin.register(Witness)
class WitnessAdmin(ExtraButtonsMixin, nested_admin.NestedModelAdmin):

    # DEFINITION OF THE MAIN FORM => Add Witness
    class Media:
        css = {"all": ("css/witness-form.css",)}
        js = ("js/witness-form.js",)

    change_form_template = "admin/form.html"

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.actions = [
            "export_selected_manifests",
            "export_selected_iiif_images",
            "export_selected_images",
            "export_annotated_imgs",
            "export_training_imgs",
            "export_training_anno",
        ]

    ordering = ("id", "place__name")
    list_per_page = 100

    # Fields that are taken into account by the search bar
    search_fields = (
        "id_nb",
        "place__name",
        "type",
        "contents__roles__person__name",
        "contents__work__title",
        "notes",
    )
    # Filters options in the sidebar
    list_filter = ("type", "digitizations__is_open", "contents__tags__label")
    # Attributes to be excluded from the form fields
    exclude = ("slug", "created_at", "updated_at")
    # Dropdown fields
    autocomplete_fields = ("place", "volume", "edition")

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
                    "edition",
                    ("volume_nb", "volume_title"),
                    "link",
                    "is_public",
                ]
            },
        ),
    )

    # MARKER SUB-FORMS existing within the Witness form
    inlines = [DigitizationInline, ContentInline]

    # def get_inline_instances(self, request, obj=None):
    #     # TODO to delete?
    #     # called every time the form is rendered without need of refreshing the page
    #     inline_instances = super().get_inline_instances(request, obj)
    #
    #     return inline_instances

    # MARKER SAVING METHODS

    def save_model(self, request, obj, form, change):
        # called on submission of form
        if not obj.user:
            obj.user = request.user
        obj.save()

        flash_msg = ""

        # it can't have more than 5 digits per witness, each digit can have only one image field
        for nb in range(0, 4):
            digit_id = request.POST.get(f"digitizations-{nb}-id", None)
            if digit_id:
                # TODO don't save again digit that were already treated
                continue
            digit_type = request.POST.get(f"digitizations-{nb}-digit_type", None)
            files = request.FILES.getlist(f"digitizations-{nb}-images")

            flash_msg = (
                "The image conversion and annotation process is underway. Please wait a few moments."
                if APP_LANG == "en"
                else "Le processus de téléchargement et d'annotation est en cours. Veuillez patienter quelques instants."
            )

            if len(files):  # if images were uploaded
                for i, file in enumerate(files):
                    filename, ext = get_file_ext(file.name)
                    with open(
                        f"{IMG_PATH}/temp_{obj.get_ref()}_{digit_type}_{i}.{ext}", "wb"
                    ) as saved_file:
                        saved_file.write(file.read())

        messages.warning(request, flash_msg)

    # # # # # # # # # # # #
    # MARKER WITNESS LIST #
    # # # # # # # # # # # #

    # MARKER LIST COLUMNS
    @admin.display(description=f"{DIG} & {ANNO}")
    def digit_anno_btn(self, obj: Witness):
        digits = obj.get_digits()
        if len(digits) == 0:
            return "-"
        # To display a button in the list of witnesses to know if they were annotated or not
        return mark_safe("<br><br>".join(digit.view_btn() for digit in digits))

    @admin.display(description="IIIF manifest")
    def manifest_link(self, obj):
        # To display a button in the list of witnesses to give direct link to witness manifest
        return mark_safe(
            "<br>".join(digit.manifest_link() for digit in obj.get_digits())
        )

    @admin.display(description=get_name("Work"))
    def get_works(self, obj):
        return mark_safe(obj.get_work_titles())

    @admin.display(
        description=get_name("Person", plural=True),
        # ordering="contents__roles__person__name"
    )
    def get_roles(self, obj: Witness):
        return obj.get_person_names()

    @admin.display(
        description="Dates",
    )
    def get_dates(self, obj: Witness):
        min_date, max_date = obj.get_dates()
        return format_dates(min_date, max_date)

    # list of fields that are displayed in the witnesses list view
    list_display = (
        "id",
        "id_nb",
        "place",
        "get_dates",
        "get_works",
        "get_roles",
        "digit_anno_btn",
        "user",
    )
    list_display_links = ("id_nb",)

    # MARKER LIST ACTIONS

    @admin.action(
        description=f"Export IIIF images of selected {WIT}es"
        if APP_LANG == "en"
        else f"Exporter les images IIIF des {WIT}s sélectionnés"
    )
    def export_selected_iiif_images(self, request, queryset):
        img_names = []
        for witness in queryset.exclude():
            img_names.extend(witness.get_imgs())
        img_list = [gen_iiif_url(img) for img in img_names]
        return list_to_txt(img_list, "IIIF_images")

    @admin.action(
        description=f"Export IIIF manifests of selected {WIT}es"
        if APP_LANG == "en"
        else f"Exporter les manifestes IIIF des {WIT}s sélectionnés"
    )
    def export_selected_manifests(self, request, queryset):
        manifests = []
        for witness in queryset.exclude():
            manifests.extend(
                [digit.gen_manifest_url() for digit in witness.get_digits()]
            )
        return list_to_txt(manifests, "IIIF_manifests")

    @admin.action(
        description=f"Download annotated diagram images in selected selected {WIT}es"
        if APP_LANG == "en"
        else f"Télécharger les images d'illustrations annotées des {WIT}s sélectionnés"
    )
    def export_annotated_imgs(self, request, queryset):
        if not check_selection(queryset, request):
            return

        img_urls = []
        has_annotation = False
        for witness in queryset.exclude():
            anno_wit = []
            for anno in witness.get_annotations():
                has_annotation = True
                anno_wit.extend(get_anno_images(anno))
            img_urls.extend(anno_wit)

        if not has_annotation:
            no_anno_message(request)
            return

        return zip_img(img_urls)

    @admin.action(
        description="Export annotations for segmentation model training"
        if APP_LANG == "en"
        else f"Exporter les annotations pour l'entraînement du modèle de segmentation"
    )
    def export_training_anno(self, request, queryset):
        if not check_selection(queryset, request):
            return

        dirnames_contents = {}
        has_annotation = False
        for wit in queryset.exclude():
            dirnames_contents[wit.get_ref()] = []
            for anno in wit.get_annotations():
                dirnames_contents[wit.get_ref()].extend(get_training_anno(anno))
                has_annotation = True

        if not has_annotation:
            no_anno_message(request)
            return

        return zip_dirs(dirnames_contents)

    @admin.action(
        description=f"Download full {DIG}s images in selected selected {WIT}es"
        if APP_LANG == "en"
        else f"Télécharger les images scans des {WIT}s sélectionnés"
    )
    def export_training_imgs(self, request, queryset):
        img_urls = []
        # dirnames_contents = {}
        # for wit in queryset.exclude():
        #     dirnames_contents[wit.get_ref()] = wit.get_imgs(is_abs=False)
        for witness in queryset.exclude():
            img_urls.extend(witness.get_imgs(is_abs=False))
        return zip_img(img_urls)


class WitnessInline(nested_admin.NestedStackedInline):
    # FORM contained in the Series form
    model = Witness
    extra = 0  # 1
    ordering = ("id",)
    fields = [("volume_nb", "volume_title")]
    inlines = [DigitizationInline]
