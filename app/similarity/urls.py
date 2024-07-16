from django.urls import path
from app.config.settings import APP_NAME

from app.similarity.views import *

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

# ENDPOINTS
urlpatterns += [
    path(
        f"witness/<int:wid>/regions/<int:rid>/similar-regions",
        get_similar_regions,
        name="similarity-regions",
    ),
    path(
        f"witness/<int:wid>/regions/similar-regions",
        get_similar_regions,
        name="witness-similarity-regions",
    ),
    path(
        f"witness/<int:wid>/regions/<int:rid>/query-images",
        get_query_images,
        name="query-images",
    ),
    path(
        f"witness/<int:wid>/regions/query-images",
        get_query_images,
        name="witness-query-images",
    ),
    path(
        f"witness/<int:wid>/regions/<int:rid>/similarity-page",
        get_similarity_page,
        name="similarity-page",
    ),
    path(
        f"witness/<int:wid>/regions/similarity-page",
        get_similarity_page,
        name="witness-similarity-page",
    ),
    path(f"save-category", save_category, name="save-category"),
    path(f"get-categories", get_categories, name="get-categories"),
]
