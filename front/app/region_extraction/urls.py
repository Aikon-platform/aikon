from django.urls import path

from app.config.settings import APP_NAME

from app.region_extraction.views import *

app_name = "region_extraction"

urlpatterns = [
    path(
        f"{APP_NAME}/extract-regions/<str:digit_ref>",
        send_region_extraction,
        name="send-region-extraction",
    ),
    path(
        f"{APP_NAME}/regions/notify",
        receive_region_extraction_notification,
        name="notify-regions",
    ),
    path(
        f"{APP_NAME}/witness/<int:wit_id>/regions/extract",
        witness_region_extraction,
        name="witness-region-extraction",
    ),
]
