from django.urls import path
from app.config.settings import APP_NAME
from app.webapp.views import *
from app.webapp.views.users import *

app_name = "webapp"

# TODO delete the unused endpoints
urlpatterns = [
    path("", admin_app, name="home"),
    path(f"{APP_NAME}/logout", logout_view, name="logout"),
    path(f"{APP_NAME}/rgpd", rgpd),
    path(
        f"{APP_NAME}/<str:regions_ref>/show/",
        show_regions,
        name="show-regions",
    ),
    path(
        f"{APP_NAME}/<str:regions_ref>/show-all-regions",
        show_all_regions,
        name="show-all-regions",
    ),
    path(
        f"{APP_NAME}/export-regions/<str:regions_ref>",
        export_all_regions,
        name="export-regions",
    ),
    path(
        f"{APP_NAME}/export-selected-regions",
        export_selected_regions,
        name="export-selected-regions",
    ),
    path(
        f"{APP_NAME}/<str:regions_ref>/list/",
        get_regions_img_list,
        name="regions-list",
    ),
    path(
        f"{APP_NAME}/annotations/<int:regions_id>",
        witness_sas_annotations,
        name="witness-annotations",
    ),
    path(
        f"{APP_NAME}/test/<str:wit_ref>",
        test,
        name="test",
    ),
    path(
        f"{APP_NAME}/test",
        test,
        name="test",
    ),
    path(
        # digit_ref = {wit_abbr}{wit_id}_{digit_abbr}{digit_id}
        f"{APP_NAME}/iiif/<str:digit_ref>/manifest.json",
        manifest_digitization,
        name="manifest-digitization",
    ),
    path(
        # regions_ref = {wit_abbr}{wit_id}_{digit_abbr}{digit_id}_anno{regions_id}
        f"{APP_NAME}/iiif/<str:version>/<str:regions_ref>/manifest.json",
        manifest_regions,
        name="manifest-regions",
    ),
    path(
        f"{APP_NAME}/iiif/populate/<int:regions_id>",
        populate_annotation,
        name="populate-annotation",
    ),
    path(
        f"{APP_NAME}/iiif/validate/<str:regions_ref>",
        validate_regions,
        name="validate-regions",
    ),
    path(
        f"{APP_NAME}/iiif/<str:version>/<str:regions_ref>/list/anno-<int:canvas_nb>.json",
        canvas_annotations,
        name="canvas-annotations",
    ),
    path(
        f"{APP_NAME}/iiif/regions/<int:regions_id>",
        export_regions_img,
        name="regions-imgs",
    ),
    path(
        f"{APP_NAME}/iiif/digit-regions/<int:digit_id>",
        export_digit_img,
        name="digitization-imgs",
    ),
    path(
        f"{APP_NAME}/iiif/witness-annotation/<int:wit_id>",
        export_wit_img,
        name="witness-imgs",
    ),
    path(
        f"{APP_NAME}/index-witness/<int:wit_id>",
        index_witness_regions,
        name="index-witness-regions",
    ),
    path(
        f"{APP_NAME}/reindex-regions/<str:obj_ref>",
        reindex_regions,
        name="reindex-regions",
    ),
    path(
        f"{APP_NAME}/index-regions/<str:regions_ref>",
        index_regions,
        name="index-regions",
    ),
    path(
        f"{APP_NAME}/index-regions",
        index_regions,
        name="index-regions",
    ),
    path(
        f"{APP_NAME}/delete-annotations-regions/<str:obj_ref>",
        delete_annotations_regions,
        name="delete-annotations-regions",
    ),
    path(
        f"{APP_NAME}/autocomplete/place/",
        PlaceAutocomplete.as_view(),
        name="place-autocomplete",
    ),
    path(
        f"{APP_NAME}/autocomplete/language/",
        LanguageAutocomplete.as_view(),
        name="language-autocomplete",
    ),
    path(
        f"{APP_NAME}/autocomplete/document-set/",
        DocumentSetAutocomplete.as_view(),
        name="document-set-autocomplete",
    ),
    path(
        f"{APP_NAME}/set-title/<int:set_id>",
        set_title,
        name="set-title",
    ),
    path("retrieve_place_info/", retrieve_place_info, name="retrieve-place-info"),
    path("eida/iiif/auto/manuscript/<str:old_id>/manifest.json", legacy_manifest),
    path(f"{APP_NAME}/advanced-search/", advanced_search, name="advanced-search"),
    path(
        f"{APP_NAME}/autocomplete/edition/",
        EditionAutocomplete.as_view(),
        name="edition-autocomplete",
    ),
    path(
        f"{APP_NAME}/api-progress",
        api_progress,
        name="api-progress",
    ),
    path(
        f"{APP_NAME}/cancel-treatment/<str:treatment_id>",
        cancel_treatment,
        name="cancel-treatment",
    ),
    path(
        f"{APP_NAME}/relaunch-treatment/<str:treatment_id>",
        relaunch_treatment,
        name="relaunch-treatment",
    ),
]

# ADMIN VIEWS
urlpatterns += [
    path(f"witness/", WitnessList.as_view(), name="witness_list"),
    path(f"witness/<int:id>/", WitnessView.as_view(), name="witness_view"),
    # path(f"witness/add/", WitnessCreate.as_view(), name="witness_create"),
    path(
        f"witness/<int:id>/change/",
        WitnessUpdate.as_view(),
        name="witness_update",
    ),
    path(
        f"witness/<int:wid>/regions/<int:rid>/",
        RegionsView.as_view(),
        name="regions_view",
    ),
    path(
        f"witness/<int:id>/regions/",
        WitnessRegionsView.as_view(),
        name="witness_regions_view",
    ),
    path(f"treatment/", TreatmentList.as_view(), name="treatment_list"),
    path(f"treatment/add/", TreatmentCreate.as_view(), name="treatment_create"),
    path(f"work/", WorkList.as_view(), name="work_list"),
    path(f"series/", SeriesList.as_view(), name="series_list"),
]

# ENDPOINTS
urlpatterns += [
    path(
        f"document-set/add",
        save_document_set,
        name="new-document-set",
    ),
    path(
        f"document-set/<int:dsid>/change",
        save_document_set,
        name="change-document-set",
    ),
    path(
        f"witness/<int:wid>/regions/<int:rid>/canvas",
        get_canvas_regions,
        name="canvas_regions",
    ),
    path(
        f"witness/<int:wid>/regions/canvas",
        get_canvas_witness_regions,
        name="canvas_witness_regions",
    ),
    path(
        f"witness/<int:wid>/regions/add",
        create_manual_regions,
        name="witness_manual_regions",
    ),
    path(
        f"witness/<int:wid>/digitization/<int:did>/regions/add",
        create_manual_regions,
        name="digit_manual_regions",
    ),
    path(
        f"witness/<int:wid>/regions/<int:rid>/add",
        create_manual_regions,
        name="regions_manual_regions",
    ),
    path(
        f"regions/<int:rid>/delete",
        delete_regions,
        name="delete_regions",
    ),
    path(
        f"regions/export",
        export_regions,
        name="export_regions",
    ),
]

# SEARCH
urlpatterns += [
    # path("search/<record-name>/", search_<record-name>, name="search-<record-name>"),
    path("search/witness/", search_witnesses, name="search-witnesses"),
    path("search/treatment/", search_treatments, name="search-treatments"),
    path("search/work/", search_works, name="search-works"),
    path("search/series/", search_series, name="search-series"),
]
