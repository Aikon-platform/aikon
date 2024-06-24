from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, register_converter

from app.config.settings import APP_NAME, MEDIA_URL, MEDIA_ROOT, DEBUG

from app.vectorization.views import (
    show_vectorization,
    receive_vecto,
    show_crop_vecto,
    export_selected_imgs_and_svgs,
    export_all_images_and_svgs,
    send_vectorization,
    smash_and_relauch_vecto,
)


class ListConverter:
    regex = r"[^/]+(?:\+[^/]+)*"

    def to_python(self, value):
        return value.split("+")

    def to_url(self, value):
        return "+".join(value)


register_converter(ListConverter, "list")


urlpatterns = [
    path(
        f"{APP_NAME}/<str:anno_ref>/show-vectorization",
        show_vectorization,
        name="show-vectorization",
    ),
    path(
        f"{APP_NAME}/receive-vecto",
        receive_vecto,
        name="receive-vecto",
    ),
    path(
        f"{APP_NAME}/img-and-svg/<str:img_file>/<str:coords>/<str:anno>/<int:canvas_nb>",
        show_crop_vecto,
        name="img-and-svg",
    ),
    path(
        f"{APP_NAME}/export-img-and-svg",
        export_selected_imgs_and_svgs,
        name="export-img-and-svg",
    ),
    path(
        f"{APP_NAME}/export-all-imgs-and-svgs/<str:anno_ref>",
        export_all_images_and_svgs,
        name="export-all-imgs-and-svgs",
    ),
    path(
        f"{APP_NAME}/run-vectorization/<str:anno_ref>",
        send_vectorization,
        name="run-vectorization",
    ),
    path(
        f"{APP_NAME}/smash-and-relaunch-vecto/<str:anno_ref>",
        smash_and_relauch_vecto,
        name="smash-and-relaunch-vecto",
    ),
]

urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)

import debug_toolbar

urlpatterns += [
    path("__debug__/", include(debug_toolbar.urls)),
]
