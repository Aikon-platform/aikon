from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from vhs import settings
from vhsapp.utils.constants import APP_NAME, MANIFEST_AUTO, MANIFEST_V2

from vhsapp.views import (
    show_witness,
    admin_vhs,
    manifest_volume,
    manifest_manuscript,
    populate_annotation,
    canvas_annotations,
    export_anno_img,
    witness_annotations,
    validate_annotation,
)


urlpatterns = [
    path("", admin_vhs, name="admin-vhs"),
    path(f"{APP_NAME}-admin/", admin.site.urls),
    path(
        f"{APP_NAME}/<str:wit_type>/<int:wit_id>/show/",
        show_witness,
        name="show-witness",
    ),
    path(
        f"{APP_NAME}/<str:wit_type>/<int:wit_id>/annotations/",
        witness_annotations,
        name="witness-annotations",
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
        f"{APP_NAME}/iiif/{MANIFEST_AUTO}/<str:wit_type>/<int:wit_id>/annotation/",
        export_anno_img,
        name="annotation-auto",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]
