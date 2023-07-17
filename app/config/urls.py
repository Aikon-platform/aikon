from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from app.config.settings import APP_NAME, MEDIA_URL, MEDIA_ROOT, DEBUG
from app.webapp.utils.constants import MANIFEST_V1, MANIFEST_V2

from app.webapp.views import (
    show_witness,
    admin_app,
    manifest_volume,
    manifest_manuscript,
    populate_annotation,
    PlaceAutocomplete,
    canvas_annotations,
    export_anno_img,
    witness_sas_annotations,
    test,
    validate_annotation,
)


urlpatterns = [
    path("", admin_app, name="admin-config"),
    path(f"{APP_NAME}-admin/", admin.site.urls),
    path(
        f"{APP_NAME}/<str:wit_type>/<int:wit_id>/show/",
        show_witness,
        name="show-witness",
    ),
    path(
        f"{APP_NAME}/<str:wit_type>/<int:wit_id>/annotations/",
        witness_sas_annotations,
        name="witness-annotations",
    ),
    path(
        f"{APP_NAME}/<str:wit_type>/<int:wit_id>/test/",
        test,
        name="test",
    ),
    path(
        f"{APP_NAME}/iiif/<str:version>/volume/<int:wit_id>/manifest.json",
        manifest_volume,
        name="manifest-volume",
    ),
    path(  # todo : f"{APP_NAME}/iiif/<str:version>/<str:wit_type>/<int:wit_id>/manifest.json"
        f"{APP_NAME}/iiif/<str:version>/manuscript/<int:wit_id>/manifest.json",
        manifest_manuscript,
        name="manifest-manuscript",
    ),
    path(
        f"{APP_NAME}/iiif/{MANIFEST_V2}/<str:wit_type>/<int:wit_id>/populate/",
        populate_annotation,
        name="populate-annotation",
    ),
    path(
        f"{APP_NAME}/iiif/{MANIFEST_V2}/<str:wit_type>/<int:wit_id>/validate/",
        validate_annotation,
        name="validate-annotation",
    ),
    path(
        f"{APP_NAME}/iiif/<str:version>/<str:wit_type>/<int:wit_id>/list/anno-<int:canvas>.json",
        canvas_annotations,
        name="canvas-annotations",
    ),
    path(
        f"{APP_NAME}/iiif/{MANIFEST_V1}/<str:wit_type>/<int:wit_id>/annotation/",
        export_anno_img,
        name="annotation-auto",
    ),
    path(
        f"{APP_NAME}/autocomplete/place/",
        PlaceAutocomplete.as_view(),
        name="place-autocomplete",
    ),
]

if DEBUG:
    urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)
    # urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]
