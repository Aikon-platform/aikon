import json
import os
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404

from app.config.settings import (
    APP_URL,
    APP_NAME,
    CANTALOUPE_APP_URL,
    ADDITIONAL_MODULES,
)
from app.webapp.utils.iiif import gen_iiif_url
from app.webapp.models.document_set import DocumentSet
from app.webapp.models.region_extraction import RegionExtraction
from app.webapp.models.witness import Witness
from app.webapp.models.digitization import Digitization
from app.webapp.utils.functions import (
    zip_img,
    get_files_in_dir,
    get_files_with_prefix,
    parse_img_ref,
    safe_int,
)
from app.webapp.utils.data_transfer import (
    get_transfer_model,
    serialize_record,
)
from app.webapp.utils.iiif.annotation import get_record_annotations
from app.webapp.utils.paths import IMG_PATH
from app.webapp.utils.logger import log
from app.similarity.utils import export_pairs


def get_json_record(request, model_name, rid):
    """Raw serialization of any transferable record for cross-instance import"""
    try:
        model = get_transfer_model(model_name)
    except (ValueError, LookupError):
        return JsonResponse(
            {"error": f"Unknown record type '{model_name}'"}, status=404
        )
    record = get_object_or_404(model, pk=rid)
    return JsonResponse(serialize_record(record), safe=False)


def export_region_extraction(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)
    data = json.loads(request.body.decode("utf-8"))
    region_extraction_ref = data.get("regionExtractionRef")

    urls_list = []
    for ref in region_extraction_ref:
        try:
            wit, digit, canvas, coord = ref.split("_")
            urls_list.append(
                gen_iiif_url(f"{wit}_{digit}_{canvas}.jpg", 2, f"{coord}/full/0")
            )
        except Exception as e:
            log(f"[export_region_extraction] Couldn't parse {ref} for export", e)

    return zip_img(urls_list)


def iter_docset_files(doc_set):
    """
    Yield (arcname, content) for every file of a document set export.
    content is a Path (written from disk, never loaded in memory) or a str.
    Hierarchy:
    [Document set: Root folder]
    |-- [Witness: one folder each]
    |   |-- metadata.json
    |   |-- [digitizations]
    |   |   |-- manifest{digit_id}.json
    |   |   |-- [image files]
    |   |-- [RegionExtraction: one folder each]
    |   |   |-- annotations.json
    |   |   |-- coco.json
    |   |   |-- [vectorization]
    |   |   |   |-- metadata.json
    |   |   |   |-- figure.svg [for each vectorized file]
    |-- similarity/pairs.json [set-level, all digits inside the set]
    """
    for w in doc_set.all_witnesses():
        # TODO: if witness is private, check if witness made by user of the same group
        if not w.is_public:
            continue
        base = f"witness{w.id}"
        yield f"{base}/metadata.json", json.dumps(serialize_record(w), default=str)

        for d in w.get_digits():
            yield f"{base}/digitizations/manifest{d.id}.json", json.dumps(
                d.get_manifest_json()
            )
            for img in d.get_imgs():
                yield f"{base}/digitizations/{img}", Path(f"{IMG_PATH}/{img}")

        for regions in w.get_region_extractions():
            r_base = f"{base}/regions{regions.id}"
            if "region_extraction" in ADDITIONAL_MODULES:
                r_json = get_region_data(w.id, regions.id)
                yield f"{r_base}/annotations.json", json.dumps(r_json)
                yield f"{r_base}/coco.json", json.dumps(gen_coco_data(w, r_json))

            if "vectorization" in ADDITIONAL_MODULES:
                v_json = get_vecto_data(regions.id, include_svg=True)
                for v in v_json:
                    yield f"{r_base}/vectorization/{v['filename']}", v.pop("svg") or ""
                yield f"{r_base}/vectorization/metadata.json", json.dumps(v_json)

    if "similarity" in ADDITIONAL_MODULES:
        yield "similarity/pairs.json", json.dumps(
            export_pairs(doc_set.get_digit_ids())["pairs"]
        )


def export_docset(request, dsid):
    """Streaming ZIP export of a document set"""
    if request.method != "GET":
        return JsonResponse({"error": "Invalid request method"}, status=400)
    doc_set = get_object_or_404(DocumentSet, id=dsid)

    tmp = tempfile.TemporaryFile()
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for arcname, content in iter_docset_files(doc_set):
            try:
                if isinstance(content, Path):
                    z.write(content, arcname)
                else:
                    z.writestr(arcname, content)
            except (FileNotFoundError, OSError) as e:
                log(f"[export_docset] Could not add {arcname} to archive", e)
    tmp.seek(0)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return FileResponse(
        tmp,
        as_attachment=True,
        filename=f"export_docset{dsid}_{timestamp}.zip",
        content_type="application/zip",
    )


def gen_coco_data(witness, regions_data):
    """
    Given a Witness and its RegionExtraction data, shapes the extracted regions
    as a COCO-formatted object (image dimensions read from digitization json)
    """
    images = [
        {
            "id": os.path.splitext(i["name"])[0],
            "file_name": i["name"],
            "width": i["w"],
            "height": i["h"],
        }
        for d in witness.get_digits()
        for i in d.get_imgs(with_meta=True)
    ]

    # Not exactly sure what to do with categories
    category_id = 1
    annotations = [
        {
            "id": crop["id"],
            "image_id": crop["img"],
            "category_id": category_id,
            "bbox": list(map(int, crop["xywh"])),
            "area": int(crop["xywh"][2]) * int(crop["xywh"][3]),
            "iscrowd": 0,
        }
        for crop_dict in (regions_data.get("extracted_crops") or {}).values()
        for crop in crop_dict.values()
    ]

    return {
        "images": images,
        "annotations": annotations,
        "categories": [{"id": category_id, "name": "Extracted region"}],
    }


def get_region_data(wid, rid):
    result = {}
    witness = get_object_or_404(Witness, id=wid)
    if witness.is_public:
        regions = get_object_or_404(RegionExtraction, id=rid)
        result = {
            "manifest": regions.get_manifest_url(),
            "extracted_crops": get_record_annotations(record=regions, as_json=True),
        }
    return result


def get_json_digit_regions(request, wid, did):
    """All bbox annotations on a digitization's canvases, with or without RegionExtraction"""
    witness = get_object_or_404(Witness, id=wid)
    if not witness.is_public:
        return JsonResponse({})
    digit = get_object_or_404(Digitization, id=did, witness=witness)
    return JsonResponse(
        {
            "manifest": digit.get_manifest_url(),
            "extracted_crops": get_record_annotations(digit, as_json=True),
        }
    )


def get_json_docset_simil(request, dsid):
    if request.method != "GET":
        return JsonResponse({"error": "Invalid request method"}, status=400)
    doc_set = get_object_or_404(DocumentSet, id=dsid)
    after_id = safe_int(request.GET.get("after")) or 0
    limit = min(safe_int(request.GET.get("limit")) or 1000, 5000)
    return JsonResponse(export_pairs(doc_set.get_digit_ids(), after_id, limit))


def create_json_vecto_element(svg_filename, include_svg, subfolder_name=None):
    from app.vectorization.const import SVG_PATH

    svg_fullpath = (
        f"{SVG_PATH}/{subfolder_name}/{svg_filename}"
        if subfolder_name
        else f"{SVG_PATH}/{svg_filename}"
    )
    filename = subfolder_name + svg_filename if subfolder_name else svg_filename
    parsed = parse_img_ref(svg_filename)
    with open(svg_fullpath, "r", encoding="utf-8") as f:
        return {
            "filename": filename,
            "img_url": f"{CANTALOUPE_APP_URL}/iiif/2/wit{parsed['wit']}_img{parsed['digit']}_{parsed['canvas']}.jpg/{','.join(parsed['coord'])}/full/0/default.jpg",
            "svg": f.read() if include_svg else None,
        }


def get_vecto_data(rid, include_svg=True):
    # Inspired from 'get_vectorized_images' in 'vectorization/views.py'
    from app.vectorization.const import SVG_PATH

    q_r = get_object_or_404(RegionExtraction, pk=rid)
    v_imgs = []
    # Mirroring what happens with vectorization view:
    # First look in folder named after regions_ref, then try with digit_ref
    try:
        r_ref = q_r.get_ref()
        for file in get_files_in_dir(f"{SVG_PATH}/{r_ref}"):
            v_imgs.append(
                create_json_vecto_element(file, include_svg, subfolder_name=r_ref)
            )
    except ValueError:
        digit_ref = q_r.get_ref().split("_anno")[0]
        for file_path in get_files_with_prefix(SVG_PATH, digit_ref):
            v_imgs.append(create_json_vecto_element(file_path, include_svg))

    return v_imgs


### JSON ENCLOSING ###
def get_json_regions(request, wid, rid):
    if request.method == "GET":
        return JsonResponse(get_region_data(wid, rid), safe=False)
    return JsonResponse({"error": "Invalid request method"}, status=400)


def get_json_witness(request, wid):
    if request.method == "GET":
        witness = get_object_or_404(Witness, id=wid)
        if not witness.is_public:
            return JsonResponse({})
        try:
            return JsonResponse(serialize_record(witness), safe=False)
        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=400)


def get_json_vecto(request, wid, rid):
    if request.method == "GET":
        witness = get_object_or_404(Witness, id=wid)
        if witness.is_public:
            return JsonResponse(get_vecto_data(rid, include_svg=True), safe=False)
    return JsonResponse({"error": "Invalid request method"}, status=400)


def get_json_document_set(request, dsid):
    if request.method == "GET":
        doc_set = get_object_or_404(DocumentSet, id=dsid)
        ds_data = {
            w.id: f"{APP_URL}/{APP_NAME}/witness/{w.id}/json"
            for w in doc_set.all_witnesses()
            if w.is_public
        }
        if "similarity" in ADDITIONAL_MODULES and ds_data:
            ds_data[
                "similarity"
            ] = f"{APP_URL}/{APP_NAME}/document-set/{dsid}/json/similarity"
        return JsonResponse(ds_data, safe=False)
    return JsonResponse({"error": "Invalid request method"}, status=400)
