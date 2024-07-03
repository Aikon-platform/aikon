from django.urls import path

from app.config.settings import APP_NAME

from app.similarity.views import (
    receive_similarity,
    send_similarity,
    show_similarity,
    compute_score,
    retrieve_category,
    save_category,
)

app_name = "similarity"

urlpatterns = [
    path(
        f"{APP_NAME}/similarity",
        receive_similarity,
        name="receive-similarity",
    ),
    path(
        f"{APP_NAME}/run-similarity/<list:regions_refs>",  # regions_refs = regions_ref+regions_ref+regions_ref
        send_similarity,
        name="send-similarity",
    ),
    path(
        f"{APP_NAME}/<str:regions_ref>/show-similarity",  # regions_refs = regions_ref+regions_ref+regions_ref
        show_similarity,
        name="show-similarity",
    ),
    path(
        f"{APP_NAME}/compute-score",
        compute_score,
        name="compute-score",
    ),
    path(f"{APP_NAME}/retrieve-category/", retrieve_category, name="retrieve-category"),
    path(f"{APP_NAME}/save-category/", save_category, name="save-category"),
]
