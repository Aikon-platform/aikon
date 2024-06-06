from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, register_converter

from app.config.settings import APP_NAME, MEDIA_URL, MEDIA_ROOT, DEBUG

from app.webapp.views import (
    show_regions,
    admin_app,
    manifest_digitization,
    manifest_regions,
    populate_annotation,
    PlaceAutocomplete,
    canvas_annotations,
    export_regions_img,
    witness_sas_annotations,
    test,
    validate_regions,
    receive_regions_file,
    send_regions_extraction,
    export_wit_img,
    export_digit_img,
    reindex_regions,
    regions_deletion_extraction,
    retrieve_place_info,
    rgpd,
    LanguageAutocomplete,
    legacy_manifest,
    index_regions,
    delete_annotations_regions,
    get_regions_img_list,
    send_similarity,
    receive_similarity,
    show_similarity,
    task_status,
    compute_score,
    show_all_regions,
    export_all_crops,
    export_selected_crops,
    retrieve_category,
    save_category,
    show_vectorization,
)


class ListConverter:
    regex = r"[^/]+(?:\+[^/]+)*"

    def to_python(self, value):
        return value.split("+")

    def to_url(self, value):
        return "+".join(value)


register_converter(ListConverter, "list")


urlpatterns = [
    path("", admin_app, name="admin-config"),
    path(f"{APP_NAME}/rgpd", rgpd),
    path(f"{APP_NAME}-admin/", admin.site.urls),
    path(
        f"{APP_NAME}/<str:regions_ref>/show/",
        show_regions,
        name="show-regions",
    ),
    path(
        f"{APP_NAME}/<str:regions_ref>/list/",
        get_regions_img_list,
        name="regions-list",
    ),
    path(
        f"{APP_NAME}/annotations/<int:regions_id>",
        witness_sas_annotations,
        name="witness-annotations",
    ),
    path(
        f"{APP_NAME}/test/<str:wit_ref>",
        test,
        name="test",
    ),
    path(
        f"{APP_NAME}/test",
        test,
        name="test",
    ),
    path(
        # digit_ref = {wit_abbr}{wit_id}_{digit_abbr}{digit_id}
        f"{APP_NAME}/iiif/<str:digit_ref>/manifest.json",
        manifest_digitization,
        name="manifest-digitization",
    ),
    path(
        # regions_ref = {wit_abbr}{wit_id}_{digit_abbr}{digit_id}_anno{regions_id}
        f"{APP_NAME}/iiif/<str:version>/<str:regions_ref>/manifest.json",
        manifest_regions,
        name="manifest-regions",
    ),
    path(
        f"{APP_NAME}/iiif/populate/<int:regions_id>",
        populate_annotation,
        name="populate-annotation",
    ),
    path(
        f"{APP_NAME}/iiif/validate/<str:regions_ref>",
        validate_regions,
        name="validate-regions",
    ),
    path(
        f"{APP_NAME}/iiif/<str:version>/<str:regions_ref>/list/anno-<int:canvas_nb>.json",
        canvas_annotations,
        name="canvas-annotations",
    ),
    path(
        f"{APP_NAME}/iiif/regions/<int:regions_id>",
        export_regions_img,
        name="regions-imgs",
    ),
    path(
        f"{APP_NAME}/iiif/digit-regions/<int:digit_id>",
        export_digit_img,
        name="digitization-imgs",
    ),
    path(
        f"{APP_NAME}/iiif/witness-annotation/<int:wit_id>",
        export_wit_img,
        name="witness-imgs",
    ),
    path(
        f"{APP_NAME}/autocomplete/place/",
        PlaceAutocomplete.as_view(),
        name="place-autocomplete",
    ),
    path(
        f"{APP_NAME}/autocomplete/language/",
        LanguageAutocomplete.as_view(),
        name="language-autocomplete",
    ),
    path("retrieve_place_info/", retrieve_place_info, name="retrieve-place-info"),
    path(
        f"{APP_NAME}/similarity",
        receive_similarity,
        name="receive-similarity",
    ),
    path(
        f"{APP_NAME}/run-similarity/<list:regions_refs>",  # regions_refs = regions_ref+regions_ref+regions_ref
        send_similarity,
        name="send-similarity",
    ),
    path(
        f"{APP_NAME}/<str:regions_ref>/show-similarity",  # regions_refs = regions_ref+regions_ref+regions_ref
        show_similarity,
        name="show-similarity",
    ),
    path(
        f"{APP_NAME}/task-status/<str:task_id>/",
        task_status,
        name="task-status",
    ),
    path(
        f"{APP_NAME}/compute-score",
        compute_score,
        name="compute-score",
    ),
    path(
        f"{APP_NAME}/extract-regions/<str:digit_ref>",
        send_regions_extraction,
        name="send-regions-extraction",
    ),
    path(
        f"{APP_NAME}/get-regions/<str:digit_ref>",
        receive_regions_file,
        name="receive-regions-file",
    ),
    path(
        f"{APP_NAME}/reindex-regions/<str:obj_ref>",
        reindex_regions,
        name="reindex-regions",
    ),
    path(
        f"{APP_NAME}/index-regions/<str:regions_ref>",
        index_regions,
        name="index-regions",
    ),
    path(
        f"{APP_NAME}/index-regions",
        index_regions,
        name="index-regions",
    ),
    path(
        f"{APP_NAME}/regions-deletion-extraction/<str:digit_ref>",
        regions_deletion_extraction,
        name="regions-deletion-extraction",
    ),
    path(
        f"{APP_NAME}/delete-annotations-regions/<str:obj_ref>",
        delete_annotations_regions,
        name="delete-annotations-regions",
    ),
    path(f"{APP_NAME}/retrieve-category/", retrieve_category, name="retrieve-category"),
    path(f"{APP_NAME}/save-category/", save_category, name="save-category"),
    path("eida/iiif/auto/manuscript/<str:old_id>/manifest.json", legacy_manifest),
    path(
        f"{APP_NAME}/<str:regions_ref>/show-all-regions",
        show_all_regions,
        name="show-all-regions",
    ),
    path(
        f"{APP_NAME}/export-crops/<str:regions_ref>",
        export_all_crops,
        name="export-crops",
    ),
    path(
        f"{APP_NAME}/export-selected-crops",
        export_selected_crops,
        name="export-selected-crops",
    ),
    path(
        f"{APP_NAME}/<str:regions_ref>/show-vectorization",
        show_vectorization,
        name="show-vectorization",
    ),
]

urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)

import debug_toolbar

urlpatterns += [
    path("__debug__/", include(debug_toolbar.urls)),
]
