from django.urls import path, include, register_converter
from django.conf.urls.static import static
from django.conf.urls import handler404, handler500, handler403, handler400
from django.contrib.auth import views as auth_views
from django.urls.converters import get_converters

from app.config.settings import (
    MEDIA_URL,
    MEDIA_ROOT,
    ADDITIONAL_MODULES,
    DEBUG,
    APP_NAME,
    INSTALLED_APPS
)

from django.contrib.admin import site as admin_site


class ListConverter:
    regex = r"[^/]+(?:\+[^/]+)*"

    def to_python(self, value):
        return value.split("+")

    def to_url(self, value):
        return "+".join(value)


if "list" not in get_converters():
    register_converter(ListConverter, "list")

# Custom error handlers
handler404 = "webapp.views.error_404"
handler500 = "webapp.views.error_500"
handler403 = "webapp.views.error_403"
handler400 = "webapp.views.error_400"


urlpatterns = [
    path(f"{APP_NAME}-admin/", admin_site.urls),
    path("", include("webapp.urls")),
    path("", include("django.contrib.auth.urls")),
]

for module in ADDITIONAL_MODULES:
    urlpatterns += [path(f"", include(f"{module}.urls"))]

if DEBUG:
    # Serve media files in development
    urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)

if "debug_toolbar" in INSTALLED_APPS:
    import debug_toolbar

    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
