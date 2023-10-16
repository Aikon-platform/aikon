from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

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
    search_similarity,
    reindex_anno,
    delete_send_anno,
)


urlpatterns = [
    path("", admin_app, name="admin-config"),
    path(f"{APP_NAME}-admin/", admin.site.urls),
    path(
        f"{APP_NAME}/show/<int:anno_id>",
        show_annotations,
        name="show-annotations",
    ),
    path(
        f"{APP_NAME}/annotations/<int:anno_id>",
        witness_sas_annotations,
        name="witness-annotations",
    ),
    path(
        f"{APP_NAME}/<str:wit_type>/<int:wit_id>/test/",
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
        # TODO enforce that the url is correctly formatted
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
        f"{APP_NAME}/iiif/validate/<int:anno_id>",
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
        f"{APP_NAME}/annotate/<int:digit_id>",
        receive_anno,
        name="receive-annotations",
    ),
    path(
        f"{APP_NAME}/run-annotation/<int:digit_id>",
        send_anno,
        name="send-annotations",
    ),
    path(
        f"{APP_NAME}/reindex-annotation/<str:anno_ref>",
        reindex_anno,
        name="reindex-annotations",
    ),
    path(
        f"{APP_NAME}/delete-run-annotation/<str:anno_ref>",
        delete_send_anno,
        name="delete-run-annotations",
    ),
    path(
        f"{APP_NAME}/search-similarity/<str:experiment_id>/",
        search_similarity,
        name="search-similarity",
    ),
]

if DEBUG:
    urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)
    # urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]
