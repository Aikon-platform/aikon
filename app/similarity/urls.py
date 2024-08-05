from django.urls import path
from app.config.settings import APP_NAME

from app.similarity.views import *

app_name = "similarity"

urlpatterns = [
    path(
        f"{APP_NAME}/get-similarity",
        receive_similarity,
        name="receive-similarity",
    ),
    path(
        f"{APP_NAME}/run-similarity/<list:regions_refs>",  # regions_refs = regions_ref+regions_ref+regions_ref
        send_similarity,
        name="send-similarity",
    ),
    path(
        f"{APP_NAME}/witness/<int:wid>/regions/<int:rid>/compared-regions",
        get_compared_regions,
        name="compared-regions",
    ),
    path(
        f"{APP_NAME}/witness/<int:wid>/regions/compared-regions",
        get_compared_regions,
        name="witness-compared-regions",
    ),
    path(
        f"{APP_NAME}/witness/<int:wid>/regions/<int:rid>/query-images",
        get_query_images,
        name="query-images",
    ),
    path(
        f"{APP_NAME}/witness/<int:wid>/regions/query-images",
        get_query_images,
        name="witness-query-images",
    ),
    path(
        f"{APP_NAME}/witness/<int:wid>/regions/<int:rid>/similar-images",
        get_similar_images,
        name="similar-images",
    ),
    path(
        f"{APP_NAME}/witness/<int:wid>/regions/similar-images",
        get_similar_images,
        name="witness-similar-region",
    ),
    path(
        f"{APP_NAME}/witness/<int:wid>/regions/<int:rid>/add-region-pair",
        add_region_pair,
        name="add-region-pair",
    ),
    path(
        f"{APP_NAME}/witness/<int:wid>/regions/add-region-pair",
        add_region_pair,
        name="add-witness-region-pair",
    ),
    path(
        f"{APP_NAME}/witness/<int:wid>/regions/<int:rid>/no-match",
        no_match,
        name="no-match",
    ),
    path(
        f"{APP_NAME}/witness/<int:wid>/regions/no-match",
        no_match,
        name="witness-no-match",
    ),
    path(f"{APP_NAME}/save-category", save_category, name="save-category"),
    path(
        f"{APP_NAME}/index-similarity/<str:regions_ref>",
        index_regions_similarity,
        name="index-similarity",
    ),
    # path(f"{APP_NAME}/similarity/delete-all", delete_all_regions_pairs, name="delete-pairs"),
]
