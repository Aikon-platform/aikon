from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, register_converter

from app.config.settings import APP_NAME, MEDIA_URL, MEDIA_ROOT, DEBUG

from app.webapp.views import (
    show_annotations,
    admin_app,
    manifest_digitization,
    manifest_annotation,
    populate_annotation,
    PlaceAutocomplete,
    canvas_annotations,
    export_anno_img,
    witness_sas_annotations,
    test,
    validate_annotation,
    receive_anno,
    send_anno,
    export_wit_img,
    export_digit_img,
    reindex_anno,
    delete_send_anno,
    retrieve_place_info,
    rgpd,
    LanguageAutocomplete,
    legacy_manifest,
    index_anno,
    delete_annotation,
    get_annos_img_list,
    send_similarity,
    receive_similarity,
    show_similarity,
    task_status,
    compute_score,
    show_all_annotations, 
)

from app.webapp.utils.functions import zip_img

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
        f"{APP_NAME}/<str:anno_ref>/show/",
        show_annotations,
        name="show-annotations",
    ),
    path(
        f"{APP_NAME}/<str:anno_ref>/list/",
        get_annos_img_list,
        name="annotation-list",
    ),
    path(
        f"{APP_NAME}/annotations/<int:anno_id>",
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
        # anno_ref = {wit_abbr}{wit_id}_{digit_abbr}{digit_id}_anno{anno_id}
        f"{APP_NAME}/iiif/<str:version>/<str:anno_ref>/manifest.json",
        manifest_annotation,
        name="manifest-annotation",
    ),
    path(
        f"{APP_NAME}/iiif/populate/<int:anno_id>",
        populate_annotation,
        name="populate-annotation",
    ),
    path(
        f"{APP_NAME}/iiif/validate/<str:anno_ref>",
        validate_annotation,
        name="validate-annotation",
    ),
    path(
        f"{APP_NAME}/iiif/<str:version>/<str:anno_ref>/list/anno-<int:canvas_nb>.json",
        canvas_annotations,
        name="canvas-annotations",
    ),
    path(
        f"{APP_NAME}/iiif/annotation/<int:anno_id>",
        export_anno_img,
        name="annotation-imgs",
    ),
    path(
        f"{APP_NAME}/iiif/digit-annotation/<int:digit_id>",
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
        f"{APP_NAME}/run-similarity/<list:anno_refs>",  # anno_refs = anno_ref+anno_ref+anno_ref
        send_similarity,
        name="send-similarity",
    ),
    path(
        f"{APP_NAME}/<str:anno_ref>/show-similarity",  # anno_refs = anno_ref+anno_ref+anno_ref
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
        f"{APP_NAME}/annotate/<str:digit_ref>",
        receive_anno,
        name="receive-annotations",
    ),
    path(
        f"{APP_NAME}/run-annotation/<str:digit_ref>",
        send_anno,
        name="send-annotations",
    ),
    path(
        f"{APP_NAME}/reindex-annotation/<str:obj_ref>",
        reindex_anno,
        name="reindex-annotations",
    ),
    path(
        f"{APP_NAME}/index-annotation/<str:anno_ref>",
        index_anno,
        name="index-annotations",
    ),
    path(
        f"{APP_NAME}/index-annotation",
        index_anno,
        name="index-annotations",
    ),
    path(
        f"{APP_NAME}/delete-run-annotation/<str:digit_ref>",
        delete_send_anno,
        name="delete-run-annotations",
    ),
    path(
        f"{APP_NAME}/delete-annotation/<str:obj_ref>",
        delete_annotation,
        name="delete-annotation",
    ),
    path("eida/iiif/auto/manuscript/<str:old_id>/manifest.json", legacy_manifest),
    path(f"{APP_NAME}/<str:anno_ref>/show-all-annotations",
        show_all_annotations,
        name="show-all-annotations"
    ),
    path(
        f"{APP_NAME}/zip-images/<str:img_list>",
        zip_img,
        name="zip-images",
    ),
]

if DEBUG:
    urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)

    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]
