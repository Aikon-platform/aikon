from django.urls import path, include, register_converter
from django.conf.urls.static import static
from django.urls import path, include

from app.config.settings import (
    MEDIA_URL,
    MEDIA_ROOT,
    ADDITIONAL_MODULES,
    DEBUG,
    APP_NAME,
)
from django.contrib.admin import site as admin_site


class ListConverter:
    regex = r"[^/]+(?:\+[^/]+)*"

    def to_python(self, value):
        return value.split("+")

    def to_url(self, value):
        return "+".join(value)


register_converter(ListConverter, "list")

urlpatterns = [
    path(f"{APP_NAME}-admin/", admin_site.urls),
    path("", include("webapp.urls")),
]

for module in ADDITIONAL_MODULES:
    urlpatterns += [path(f"{module}/", include(f"{module}.urls"))]

if DEBUG:
    # Serve media files in development
    urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)

    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]
