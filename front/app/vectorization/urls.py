from django.urls import path
from app.config.settings import APP_NAME

from app.vectorization.views import *

app_name = "vectorization"

urlpatterns = [
    path(
        f"{APP_NAME}/<str:regions_ref>/show-vectorization",
        show_vectorization,
        name="show-vectorization",
    ),
    path(
        f"{APP_NAME}/vectorization/notify",
        receive_vectorization_notification,
        name="notify-vectorization",
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
        f"{APP_NAME}/export-all-imgs-and-svgs/<int:witness_id>",
        export_all_images_and_svgs,
        name="export-all-imgs-and-svgs",
    ),
    path(
        f"{APP_NAME}/export-regions-imgs-and-svgs/<int:regions_id>",
        export_regions_images_and_svgs,
        name="export-regions-imgs-and-svgs",
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
    path(
        f"{APP_NAME}/witness/<int:wid>/regions/<int:rid>/vectorized-images",
        get_vectorized_images,
        name="vectorized-images",
    ),
    path(
        f"{APP_NAME}/witness/<int:wid>/regions/vectorized-images",
        get_vectorized_images,
        name="witness-vectorized-images",
    ),
    path(
        f"{APP_NAME}/vectorization/reset/<int:rid>",
        reset_vectorization,
        name="reset-regions-vectorization",
    ),
    path(
        f"{APP_NAME}/vectorization/reset",
        reset_vectorization,
        name="reset-all-vectorization",
    ),
]
