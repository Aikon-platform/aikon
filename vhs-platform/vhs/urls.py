from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from vhs import settings
from vhsapp.utils.constants import APP_NAME, MANIFEST_AUTO, MANIFEST_V2

from vhsapp.views import (
    show_work,
    admin_vhs,
    manifest_volume,
    manifest_manuscript,
    populate_annotation,
    annotate_work,
    annotation_auto,
    PlaceAutocomplete,
)


urlpatterns = [
    path("", admin_vhs, name="admin-vhs"),
    path(f"{APP_NAME}-admin/", admin.site.urls),
    path(f"{APP_NAME}/<str:work>/<int:id>/show/", show_work, name="show-work"),
    path(
        f"{APP_NAME}/iiif/<str:version>/volume/vol-<int:id>/manifest.json",
        manifest_volume,
        name="manifest-volume",
    ),
    path(
        f"{APP_NAME}/iiif/<str:version>/manuscript/ms-<int:id>/manifest.json",
        manifest_manuscript,
        name="manifest-manuscript",
    ),
    path(
        f"{APP_NAME}/iiif/{MANIFEST_V2}/<str:work>/<int:id>/populate/",
        populate_annotation,
        name="populate-annotation",
    ),
    path(
        f"{APP_NAME}/iiif/<str:version>/<str:work>/<str:work_abbr>-<int:id>/list/anno-<int:canvas>.json",
        annotate_work,
        name="annotate-work",
    ),
    path(
        f"{APP_NAME}/iiif/{MANIFEST_AUTO}/<str:work>/<int:id>/annotation/",
        annotation_auto,
        name="annotation-auto",
    ),
    path(
        f"{APP_NAME}/autocomplete/place/",
        PlaceAutocomplete.as_view(),
        name="place-autocomplete",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]
