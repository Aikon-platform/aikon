from django.urls import path, reverse_lazy
from app.config.settings import APP_NAME
from app.webapp.views import *
from app.webapp.views.users import *
from django.contrib.auth import views as auth_views

app_name = "webapp"

# TODO delete the unused endpoints
urlpatterns = [
    path("", admin_app, name="home"),
    path(f"{APP_NAME}/logout", logout_view, name="logout"),
    path(
        f"{APP_NAME}/password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="admin/auth/password_reset.html",
            success_url=reverse_lazy("webapp:password-reset-done"),
            email_template_name="admin/auth/password_reset_email.html",
        ),
        name="password-reset",
    ),
    path(
        f"{APP_NAME}/password-reset/done",
        auth_views.PasswordResetDoneView.as_view(
            template_name="admin/auth/password_reset_done.html"
        ),
        name="password-reset-done",
    ),
    path(
        f"{APP_NAME}/reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="admin/auth/password_reset_confirm.html",
            success_url=reverse_lazy("webapp:password-reset-complete"),
        ),
        name="password-reset-confirm",
    ),
    path(
        f"{APP_NAME}/reset-done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="admin/auth/password_reset_complete.html"
        ),
        name="password-reset-complete",
    ),
    path(f"{APP_NAME}/profile/change", edit_profile, name="edit-profile"),
    path(f"{APP_NAME}/rgpd", rgpd),
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
        f"test",
        test,
        name="test",
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
    # path(
    #     f"{APP_NAME}/iiif/digit-regions/<int:digit_id>",
    #     export_digit_img,
    #     name="digitization-imgs",
    # ),
    # path(
    #     f"{APP_NAME}/iiif/witness-annotation/<int:wit_id>",
    #     export_wit_img,
    #     name="witness-imgs",
    # ),
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
        f"{APP_NAME}/autocomplete/witness/",
        WitnessAutocomplete.as_view(),
        name="witness-autocomplete",
    ),
    path(
        f"{APP_NAME}/autocomplete/series/",
        SeriesAutocomplete.as_view(),
        name="series-autocomplete",
    ),
    path(
        f"{APP_NAME}/autocomplete/work/",
        WorkAutocomplete.as_view(),
        name="work-autocomplete",
    ),
    path(
        f"{APP_NAME}/set-title/<int:set_id>",
        set_title,
        name="set-title",
    ),
    path("retrieve_place_info/", retrieve_place_info, name="retrieve-place-info"),
    path("eida/iiif/auto/manuscript/<str:old_id>/manifest.json", legacy_manifest),
    # path(f"{APP_NAME}/advanced-search/", advanced_search, name="advanced-search"),
    path(
        f"{APP_NAME}/autocomplete/edition/",
        EditionAutocomplete.as_view(),
        name="edition-autocomplete",
    ),
    path(
        f"{APP_NAME}/treatment/<str:treatment_id>/cancel",
        cancel_treatment,
        name="cancel-treatment",
    ),
]

# DELETE VIEWS
urlpatterns += [
    path(
        f"{APP_NAME}/treatment/<str:rec_id>/delete",
        delete_treatment,
        name="delete-treatment",
    ),
    path(
        f"{APP_NAME}/documentset/<str:rec_id>/delete",
        delete_doc_set,
        name="delete-doc_set",
    ),
    path(
        f"{APP_NAME}/work/<str:rec_id>/delete",
        delete_work,
        name="delete-work",
    ),
    path(
        f"{APP_NAME}/witness/<str:rec_id>/delete",
        delete_witness,
        name="delete-witness",
    ),
    path(
        f"{APP_NAME}/series/<str:rec_id>/delete",
        delete_series,
        name="delete-series",
    ),
    path(
        f"{APP_NAME}/edition/<str:rec_id>/delete",
        delete_edition,
        name="delete-edition",
    ),
]

# ADMIN VIEWS
urlpatterns += [
    path(f"{APP_NAME}/witness/", WitnessList.as_view(), name="witness_list"),
    path(f"{APP_NAME}/witness/<int:id>/", WitnessView.as_view(), name="witness_view"),
    # path(f"witness/add/", WitnessCreate.as_view(), name="witness_create"),
    path(
        f"{APP_NAME}/witness/<int:id>/change/",
        WitnessUpdate.as_view(),
        name="witness_update",
    ),
    path(
        f"{APP_NAME}/witness/<int:wid>/regions/<int:rid>/",
        RegionsView.as_view(),
        name="regions_view",
    ),
    path(
        f"{APP_NAME}/witness/<int:id>/regions/",
        WitnessRegionsView.as_view(),
        name="witness_regions_view",
    ),
    path(f"{APP_NAME}/treatment/", TreatmentList.as_view(), name="treatment_list"),
    path(
        f"{APP_NAME}/treatment/add/", TreatmentCreate.as_view(), name="treatment_create"
    ),
    path(
        f"{APP_NAME}/treatment/<str:id>", TreatmentView.as_view(), name="treatment_view"
    ),
    path(f"{APP_NAME}/work/", WorkList.as_view(), name="work_list"),
    path(f"{APP_NAME}/series/", SeriesList.as_view(), name="series_list"),
    path(
        f"{APP_NAME}/document-set/", DocumentSetList.as_view(), name="document_set_list"
    ),
]

# ENDPOINTS
urlpatterns += [
    path(
        f"{APP_NAME}/document-set/add",
        save_document_set,
        name="new-document-set",
    ),
    path(
        f"{APP_NAME}/document-set/<int:dsid>/change",
        save_document_set,
        name="change-document-set",
    ),
    path(
        f"{APP_NAME}/witness/<int:wid>/regions/<int:rid>/canvas",
        get_canvas_regions,
        name="canvas_regions",
    ),
    path(
        f"{APP_NAME}/witness/<int:wid>/regions/canvas",
        get_canvas_witness_regions,
        name="canvas_witness_regions",
    ),
    path(
        f"{APP_NAME}/witness/<int:wid>/regions/add",
        create_manual_regions,
        name="witness_manual_regions",
    ),
    path(
        f"{APP_NAME}/witness/<int:wid>/digitization/<int:did>/regions/add",
        create_manual_regions,
        name="digit_manual_regions",
    ),
    path(
        f"{APP_NAME}/witness/<int:wid>/regions/<int:rid>/add",
        create_manual_regions,
        name="regions_manual_regions",
    ),
    path(
        f"{APP_NAME}/regions/<int:rid>/delete",
        delete_regions,
        name="delete_regions",
    ),
    path(
        f"{APP_NAME}/regions/export",
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
    path("search/documentset/", search_document_set, name="search-document-sets"),
    path("search/digitization/", search_digitizations, name="search-digitizations"),
    path("search/json-generation/", json_regeneration, name="regenerate_json"),
]

# SUPERADMIN VIEWS
urlpatterns += [
    path("superadmin/empty-works/", list_empty_works, name="empty-works"),
    path("superadmin/works/", list_works, name="list-works"),
]
