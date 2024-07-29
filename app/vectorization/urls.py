from django.conf.urls.static import static
from django.urls import path, include, register_converter

from app.config.settings import APP_NAME, MEDIA_URL, MEDIA_ROOT

from app.vectorization.views import (
    show_vectorization,
    receive_vectorization,
    show_crop_vectorization,
    export_selected_imgs_and_svgs,
    export_all_images_and_svgs,
    send_vectorization,
    smash_and_relauch_vectorization,
)

app_name = "vectorization"

urlpatterns = [
    path(
        f"{APP_NAME}/<str:regions_ref>/show-vectorization",
        show_vectorization,
        name="show-vectorization",
    ),
    path(
        f"{APP_NAME}/get-vectorization",
        receive_vectorization,
        name="get-vectorization",
    ),
    path(
        f"{APP_NAME}/img-and-svg/<str:img_file>/<str:coords>/<str:regions>/<int:canvas_nb>",
        show_crop_vectorization,
        name="img-and-svg",
    ),
    path(
        f"{APP_NAME}/export-img-and-svg",
        export_selected_imgs_and_svgs,
        name="export-img-and-svg",
    ),
    path(
        f"{APP_NAME}/export-all-imgs-and-svgs/<str:regions_ref>",
        export_all_images_and_svgs,
        name="export-all-imgs-and-svgs",
    ),
    path(
        f"{APP_NAME}/run-vectorization/<str:regions_ref>",
        send_vectorization,
        name="run-vectorization",
    ),
    path(
        f"{APP_NAME}/smash-and-relaunch-vectorization/<str:regions_ref>",
        smash_and_relauch_vectorization,
        name="smash-and-relaunch-vectorization",
    ),
]
