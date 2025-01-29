from functools import reduce

from app.config.settings import APP_LANG, ADDITIONAL_MODULES
from app.webapp.admin.digitization import DigitizationInline
from app.webapp.admin.content import ContentInline

from app.webapp.models.utils.constants import WIT, REG, DIG
from app.webapp.models.witness import Witness, get_name
from app.webapp.utils.constants import MAX_ITEMS

import nested_admin
from admin_extra_buttons.mixins import ExtraButtonsMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import admin, messages
from django.utils.safestring import mark_safe

from app.webapp.utils.iiif import gen_iiif_url
from app.webapp.utils.functions import (
    list_to_txt,
    zip_img,
    get_file_ext,
    zip_dirs,
    format_dates,
    is_in_group,
)
from app.webapp.utils.iiif.annotation import (
    get_images_annotations,
    get_training_regions,
)
from app.webapp.utils.paths import IMG_PATH


def no_regions_message(request):
    messages.warning(
        request,
        f"Please select at least one {WIT} with regions."
        if APP_LANG == "en"
        else f"Merci de sélectionner au moins un {WIT} avec des régions.",
    )


def no_digit_message(request):
    messages.warning(
        request,
        f"Please select at least one {WIT} with a digitization."
        if APP_LANG == "en"
        else f"Merci de sélectionner au moins un {WIT} avec une numérisation.",
    )


def check_selection(queryset, request):
    if len(queryset) > MAX_ITEMS:
        messages.warning(
            request,
            f"You can select up to {MAX_ITEMS} {WIT}es."
            if APP_LANG == "en"
            else f"Vous pouvez sélectionner jusqu'à {MAX_ITEMS} {WIT}s.",
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
    list_per_page = 100

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.actions = [
            "export_selected_manifests",
            "export_selected_iiif_images",
            "export_selected_images",
            "export_imgs_regions",
            "export_training_imgs",
            "export_training_regions_files",
        ]

        for module in ADDITIONAL_MODULES:
            self.actions += [f"compute_{module}"]

    ordering = ("id", "place__name")

    # Filters options in the sidebar
    list_filter = (
        "type",
        "digitizations__is_open",
        "contents__tags__label",
        "digitizations__regions__is_validated",
    )
    # Attributes to be excluded from the form fields
    exclude = ("slug", "created_at", "updated_at")

    # MARKER FORM FIELDS
    banner = (
        f"{get_name('Witness')} identification"
        if APP_LANG == "en"
        else f"Identification du {get_name('Witness')}"
    )
    fields = [
        "type",
        ("id_nb", "place"),  # place and id_nb appear on the same line
        ("page_type", "nb_pages"),  # same
        "notes",
        "edition",
        ("volume_nb", "volume_title"),
        "link",
        "is_public",
    ]
    autocomplete_fields = ("place", "volume", "edition")
    fieldsets = (
        (
            banner.capitalize(),
            {"fields": fields},
        ),
    )

    # MARKER SUB-FORMS existing within the Witness form
    inlines = [DigitizationInline, ContentInline]

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
                # TODO! don't save again digit that were already treated
                continue
            digit_type = request.POST.get(f"digitizations-{nb}-digit_type", None)
            files = request.FILES.getlist(f"digitizations-{nb}-images")

            flash_msg = (
                "The image conversion process is underway. Please wait a few moments."
                if APP_LANG == "en"
                else "Le processus de téléchargement est en cours. Veuillez patienter quelques instants."
            )

            if len(files):  # if images were uploaded
                sorted_files = sorted(files, key=lambda f: f.name)

                for i, file in enumerate(sorted_files):
                    filename, ext = get_file_ext(file.name)
                    with open(
                        f"{IMG_PATH}/temp_{obj.get_ref()}_{digit_type}_{str(i).zfill(4)}.{ext}",
                        "wb",
                    ) as saved_file:
                        saved_file.write(file.read())

        messages.warning(request, flash_msg)

    # # # # # # # # # # # #
    # MARKER WITNESS LIST #
    # # # # # # # # # # # #

    def response_add(self, request, obj, post_url_continue=None):
        return HttpResponseRedirect(reverse("webapp:witness_list"))

    def response_change(self, request, obj):
        return HttpResponseRedirect(reverse("webapp:witness_list"))

    def response_delete(self, request, obj_display, obj_id):
        return HttpResponseRedirect(reverse("webapp:witness_list"))

    # MARKER LIST COLUMNS
    @admin.display(description=f"{DIG} & {REG}")
    def digit_regions_btn(self, obj: Witness):
        # TODO check if used else delete
        digits = obj.get_digits()
        if len(digits) == 0:
            return "-"
        # To display a button in the list of witnesses to know if regions were extracted or not
        return mark_safe("<br><br>".join(digit.view_btn() for digit in digits))

    @admin.display(description="IIIF manifest")
    def manifest_link(self, obj):
        # TODO check if used else delete
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
        "digit_regions_btn",
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
        description=f"Download extracted images in selected {WIT}es"
        if APP_LANG == "en"
        else f"Télécharger les images extraites des {WIT}s sélectionnés"
    )
    def export_imgs_regions(self, request, queryset):
        if not check_selection(queryset, request):
            return

        img_urls = []
        has_regions = False
        for witness in queryset.exclude():
            regions_wit = []
            for regions in witness.get_regions():
                has_regions = True
                regions_wit.extend(get_images_annotations(regions))
            img_urls.extend(regions_wit)

        if not has_regions:
            no_regions_message(request)
            return

        return zip_img(img_urls)

    @admin.action(
        description="Export regions for object extraction model training"
        if APP_LANG == "en"
        else f"Exporter les régions pour l'entraînement du modèle d'extraction d'objets"
    )
    def export_training_regions_files(self, request, queryset):
        if not check_selection(queryset, request):
            return

        dirnames_contents = {}
        has_regions = False
        for wit in queryset.exclude():
            dirnames_contents[wit.get_ref()] = []
            for regions in wit.get_regions():
                dirnames_contents[wit.get_ref()].extend(get_training_regions(regions))
                has_regions = True

        if not has_regions:
            no_regions_message(request)
            return

        return zip_dirs(dirnames_contents)

    @admin.action(
        description=f"Download full {DIG}s images in selected {WIT}es"
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

    def get_search_results(self, request, queryset, search_term):
        from operator import or_
        from django.db.models import Q

        queryset, use_distinct = super(WitnessAdmin, self).get_search_results(
            request, queryset, search_term
        )
        search_titles = search_term.split("||")
        if search_titles:
            for title in search_titles:
                if title:
                    q_objects = [
                        Q(**{field + "__icontains": title.strip()})
                        for field in self.search_fields
                    ]
                    queryset |= self.model.objects.filter(reduce(or_, q_objects))

        return queryset, use_distinct

    # # # # # # # # # # # #
    #     PERMISSIONS     #
    # # # # # # # # # # # #

    def has_change_permission(self, request, obj=None):
        if obj is not None:
            return (
                request.user.is_superuser
                or obj.user == request.user
                or is_in_group(request.user, obj.user)
            )

    def has_view_permission(self, request, obj=None):
        if obj is not None:
            return (
                obj.user == request.user
                or obj.is_public
                or is_in_group(request.user, obj.user)
            )


class WitnessInline(nested_admin.NestedStackedInline):
    # FORM contained in the Series form
    model = Witness
    template = "admin/includes/inline_fieldset.html"
    extra = 0  # 1
    ordering = ("id",)
    fields = [("volume_nb", "volume_title")]
    inlines = [DigitizationInline]
