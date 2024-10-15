from django.urls import path

from app.config.settings import APP_NAME

from app.regions.views import *

app_name = "regions"

urlpatterns = [
    path(
        f"{APP_NAME}/extract-regions/<str:digit_ref>",
        send_regions_extraction,
        name="send-regions-extraction",
    ),
    path(
        f"{APP_NAME}/get-regions/<str:digit_ref>",
        receive_regions_file,
        name="receive-regions-file",
    ),
    path(
        f"{APP_NAME}/regions-deletion-extraction/<str:digit_ref>",
        regions_deletion_extraction,
        name="regions-deletion-extraction",
    ),
    path(
        f"{APP_NAME}/witness/<int:wit_id>/regions/extract",
        witness_regions_extraction,
        name="witness-regions-extraction",
    ),
]
