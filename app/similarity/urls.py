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
        f"witness/<int:wid>/regions/<int:rid>/compared-regions",
        get_compared_regions,
        name="compared-regions",
    ),
    path(
        f"witness/<int:wid>/regions/compared-regions",
        get_compared_regions,
        name="witness-compared-regions",
    ),
    path(
        f"witness/<int:wid>/regions/<int:rid>/query-regions",
        get_query_regions,
        name="query-regions",
    ),
    path(
        f"witness/<int:wid>/regions/query-regions",
        get_query_regions,
        name="witness-query-regions",
    ),
    path(
        f"witness/<int:wid>/regions/<int:rid>/similar-regions",
        get_similar_regions,
        name="similar-regions",
    ),
    path(
        f"witness/<int:wid>/regions/similar-regions",
        get_similar_regions,
        name="witness-similar-region",
    ),
    path(
        f"witness/<int:wid>/regions/<int:rid>/add-region-pair",
        add_region_pair,
        name="add-region-pair",
    ),
    path(
        f"witness/<int:wid>/regions/add-region-pair",
        add_region_pair,
        name="add-witness-region-pair",
    ),
    path(f"save-category", save_category, name="save-category"),
    path(
        f"index-similarity/<str:regions_ref>",
        index_regions_similarity,
        name="index-similarity",
    ),
    # path(f"similarity/delete-all", delete_all_regions_pairs, name="delete-pairs"),
]
