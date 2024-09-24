from django.urls import path, include, register_converter

from app.vectorization.views import *

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
        smash_and_relaunch_vectorization,
        name="smash-and-relaunch-vectorization",
    ),
]

urlpatterns += [
    path(
        f"witness/<int:wid>/regions/<int:rid>/vectorized-images",
        get_vectorized_images,
        name="vectorized-images",
    ),
    path(
        f"witness/<int:wid>/regions/vectorized-images",
        get_vectorized_images,
        name="witness-vectorized-images",
    ),
]
