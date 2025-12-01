import unittest

from django.test import LiveServerTestCase

from app.webapp.models.regions import Regions, get_name
from app.webapp.models.digitization import Digitization

from app.config.settings.base import APP_PORT
from app.webapp.utils.iiif.annotation import (
    get_manifest_annotations,
    has_annotation,
    get_regions_annotations,
    index_regions,
    reindex_file,
    unindex_annotation,
    index_annotations_on_canvas,
    get_annotations_per_canvas,
    format_canvas_annotations,
    format_annotation,
    set_canvas,
    get_indexed_manifests,
    index_manifest_in_sas,
    get_canvas_list,
    get_canvas_lists,
    get_indexed_canvas_annotations,
    get_coord_from_annotation,
    get_id_from_annotation,
    formatted_annotations,
    total_annotations,
    create_list_annotations,
    check_indexation,
    get_images_annotations,
    unindex_regions,
    destroy_regions,
    get_training_regions,
    process_regions,
    get_regions_urls,
)

# TODO use a test-specific aiiinotate database, migrate it and delete afterwards (can use a mongosh db.dropDatabase() command).


class AnnotationsTestCase(LiveServerTestCase):
    # force the use of APP_PORT for the LiveServerTestCase
    port = APP_PORT
    # fixtures are saved in front/app/webapp/fixtures
    # fixtures = ["Users", "Regions", "Digitization", "Witness"]
    fixtures = ["db_fixture"]

    def setUp(self):
        pass

    def test_blabla(self):
        print("blabla")

    def test_index_regions(self):
        test_regions = Regions.objects.first()
        index_regions(test_regions)

    def tearDown(self):
        pass


# def get_manifest_annotations(
# def has_annotation(regions_ref):
# def get_regions_annotations(
# def index_regions(regions: Regions):
# def reindex_file(filename):
# def unindex_annotation(annotation_id):
# def index_annotations_on_canvas(regions: Regions, canvas_nb):
# def get_annotations_per_canvas(region: Regions, last_canvas=0, specific_canvas=""):
# def format_canvas_annotations(regions: Regions, canvas_nb):
# def format_annotation(regions: Regions, canvas_nb, xywh):
# def set_canvas(seq, canvas_nb, img_name, img, version=None):
# def get_indexed_manifests():
# def index_manifest_in_sas(manifest_url, reindex=False):
# def get_canvas_list(regions: Regions, all_img=False):
# def get_canvas_lists(digit: Digitization, all_img=False):
# def get_indexed_canvas_annotations(regions: Regions, canvas_nb):
# def get_coord_from_annotation(sas_annotation):
# def get_id_from_annotation(sas_annotation):
# def formatted_annotations(regions: Regions):
# def total_annotations(regions: Regions):
# def create_list_annotations(regions: Regions):
# def check_indexation(regions: Regions, reindex=False):
# def get_images_annotations(regions: Regions):
# def unindex_regions(regions_ref, manifest_url):
# def destroy_regions(regions: Regions):
# def get_training_regions(regions: Regions):
# def process_regions(
# def get_regions_urls(regions: Regions):
