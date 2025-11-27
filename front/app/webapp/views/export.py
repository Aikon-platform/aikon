import json
import os
from datetime import datetime
from PIL import Image

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import F

from app.config.settings import (
    BASE_URL,
    APP_NAME,
    CANTALOUPE_APP_URL,
    ADDITIONAL_MODULES,
)
from app.webapp.utils.iiif import gen_iiif_url
from app.webapp.models.digitization import Digitization
from app.webapp.models.document_set import DocumentSet
from app.webapp.models.regions import Regions
from app.webapp.models.witness import Witness
from app.webapp.models.utils.constants import PDF_ABBR, MAN_ABBR
from app.webapp.utils.functions import (
    zip_files,
    zip_img,
    get_files_in_dir,
    get_files_with_prefix,
    parse_img_ref,
)
from app.webapp.utils.iiif.annotation import (
    get_regions_annotations,
)
from app.webapp.utils.paths import IMG_PATH


def export_regions(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)
    data = json.loads(request.body.decode("utf-8"))
    regions_ref = data.get("regionsRef")

    urls_list = []
    for ref in regions_ref:
        try:
            wit, digit, canvas, coord = ref.split("_")
            urls_list.append(
                gen_iiif_url(f"{wit}_{digit}_{canvas}.jpg", 2, f"{coord}/full/0")
            )
        except Exception as e:
            log(f"[export_regions] Couldn't parse {ref} for export", e)

    return zip_img(urls_list)


def export_docset(request, dsid):
    """
    Prepares a ZIP export for a document set.
    Hierarchy:
    [Document set: Root folder]
    |-- [Witness: one folder each]
    |   |-- metadata.json
    |   |-- [digitizations]
    |   |   |   |-- [each digit file (images + original format)]
    |   |-- [Regions: one folder each]
    |   |   |-- [annotations]
    |   |   |   |-- manifest.json
    |   |   |   |-- annotations.json
    |   |   |-- [similarity]
    |   |   |   |-- metadata.json
    |   |   |-- [vectorization]
    |   |   |   |-- metadata.json
    |   |   |   |-- figure.svg [for each vectorized file]
    """
    if request.method != "GET":
        return JsonResponse({"error": "Invalid request method"}, status=400)
    doc_set = get_object_or_404(DocumentSet, id=dsid)
    file_contents = []
    for w in doc_set.all_witnesses():
        # 1: Witness data (JSON)
        # TODO: If witness is private, check if witness made by user of the same group
        w_json = get_witness_data(w, json_cascade=False)
        file_contents.append((f"witness{w.id}/metadata.json", json.dumps(w_json)))

        # 1.5: Digitizations (pdf/img/json?)
        w_digits_ids = w.get_digits()
        for d in w_digits_ids:
            # Digits always have image files whatever the type
            img_files = d.get_imgs()
            for img in img_files:
                with open(f"{IMG_PATH}/{img}", "rb") as i:
                    file_contents.append(
                        (f"witness{w.id}/digitizations/{img}", i.read())
                    )
            did = d.id
            digit_type = d.get_digit_abbr()
            if digit_type == PDF_ABBR:
                with open(f"{d.pdf.path}", "rb") as p:
                    file_contents.append(
                        (
                            f"witness{w.id}/digitizations/{d.pdf.path.split('/')[-1]}",
                            p.read(),
                        )
                    )
            elif digit_type == MAN_ABBR:
                file_contents.append(
                    (
                        f"witness{w.id}/digitizations/manifest.json",
                        d.gen_manifest_json(),
                    )
                )

        r_list = w.get_regions()
        for regions in r_list:
            # 2: Annotation (JSON manifest+metadata)
            if "regions" in ADDITIONAL_MODULES:
                file_contents.append(
                    (
                        f"witness{w.id}/regions{regions.id}/manifest.json",
                        json.dumps(
                            regions.gen_manifest_json(),
                            ensure_ascii=False,
                            indent=2,
                        ),
                    )
                )
                r_json = get_region_data(w.id, regions.id)
                file_contents.append(
                    (
                        f"witness{w.id}/regions{regions.id}/annotations.json",
                        json.dumps(r_json),
                    )
                )
                coco_r_json = gen_coco_data(w_json, r_json)
                file_contents.append(
                    (
                        f"witness{w.id}/regions{regions.id}/coco.json",
                        json.dumps(coco_r_json),
                    )
                )

            # 3: Vectorizations (SVG+JSON)
            if "vectorization" in ADDITIONAL_MODULES:
                v_json = get_vecto_data(regions.id, include_svg=True)
                for v in v_json:
                    file_contents.append(
                        (
                            f"witness{w.id}/regions{regions.id}/vectorization/{v['filename']}",
                            v["svg"],
                        )
                    )
                    del v["svg"]
                file_contents.append(
                    (
                        f"witness{w.id}/regions{regions.id}/vectorization/metadata.json",
                        json.dumps(v_json),
                    )
                )

            # 4: Similarity (JSON)
            if "similarity" in ADDITIONAL_MODULES:
                s_json = get_similarity_data(w, regions.id)
                file_contents.append(
                    (
                        f"witness{w.id}/regions{regions.id}/similarity/metadata.json",
                        json.dumps(s_json),
                    )
                )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"export_docset{dsid}_{timestamp}"
    return zip_files(file_contents, archive_name)


def gen_coco_data(witness_data, regions_data):
    """
    Given resulting dicts from Regions and Witness data, shapes the Regions metadata as a COCO-formatted  object.
    """
    coco = {"images": [], "annotations": [], "categories": []}

    for (did, manifest_url) in witness_data["digitizations"].items():
        w = get_object_or_404(Witness, id=witness_data["id"])
        imgs = w.get_imgs()
        for path in imgs:
            img = Image.open(f"{IMG_PATH}/{path}")
            try:
                h, w = int(img["height"]), int(img["width"])
            except TypeError:
                h, w = img.height, img.width
            image_entry = {
                "id": os.path.splitext(path)[0],
                "file_name": path,
                "width": w,
                "height": h,
            }
            coco["images"].append(image_entry)

    # Not exacttly sure what to do with categories
    category_id = 1
    coco["categories"].append({"id": category_id, "name": "Extracted region"})

    crops = regions_data.get("extracted_crops", {})
    for canvas_id, crop_dict in crops.items():
        for crop_key, crop_data in crop_dict.items():
            xywh = list(map(int, crop_data["xywh"]))
            bbox = xywh
            area = bbox[2] * bbox[3]
            annotation = {
                "id": crop_data["id"],
                "image_id": crop_data["img"],
                "category_id": category_id,
                "bbox": bbox,
                "area": area,
                "iscrowd": 0,
            }
            coco["annotations"].append(annotation)

    return coco


def get_region_data(wid, rid):
    result = {}
    witness = get_object_or_404(Witness, id=wid)
    if witness.is_public:
        annos = get_regions_annotations(
            regions=get_object_or_404(Regions, id=rid), as_json=True
        )
        result = {
            "manifest": get_object_or_404(Regions, pk=rid).gen_manifest_url(),
            "extracted_crops": annos,
        }
    return result


def get_similarity_data(witness: Witness, region_id: str, user_id: int = None) -> dict:
    from app.similarity.utils import (
        get_best_pairs,
        get_region_pairs_with,
        get_compared_regions_ids,
        get_regions_q_imgs,
    )

    q_imgs_set = set()
    keys = [
        "score",
        "img1",
        "img2",
        "regions1",
        "regions2",
        "category",
        "category_x",
        "manual",
    ]

    q_imgs_set.update(get_regions_q_imgs(region_id, witness.id))
    q_imgs = sorted(list(q_imgs_set))

    regions_ids = get_compared_regions_ids(region_id)

    if not regions_ids:
        return {}

    result = {}
    for q_img in q_imgs:
        pairs = get_region_pairs_with(
            q_img,
            query_regions_ids=[region_id],
            target_regions_ids=regions_ids,
        )

        best_pairs = get_best_pairs(
            q_img,
            pairs,
            excluded_categories=set(),
            user_id=user_id,
            topk=None,
            export=True,
        )

        dict_pairs = [dict(zip(keys, p)) for p in best_pairs]
        result[q_img] = dict_pairs

    return result


def get_witness_data(witness, json_cascade=True):
    wid = witness.id
    w_json_raw = witness.json
    fields = {
        "id",
        "img",
        "iiif",
        "user",
        "user_id",
        "title",
        "metadata",
        "is_public",
        "updated_at",
    }
    w_json = {k: v for k, v in w_json_raw.items() if k in fields}

    # Digitizations data (as manifests)
    w_digits_ids = witness.get_digits()
    w_digits_manifs = {
        "digitizations": dict(
            Digitization.objects.filter(id__in=w_digits_ids)
            .annotate(manifest_json=F("json__url"))
            .values_list("id", "manifest_json")
        )
    }

    w_regions = witness.get_regions()
    w_reg_processes = {}
    for r in w_regions:
        reg_raw_json = r.to_json()
        del reg_raw_json["class"]
        del reg_raw_json["type"]
        w_reg_processes[r.id] = reg_raw_json
        w_reg_processes[r.id]["treatments"] = {}

        if json_cascade:
            # 3 : Regions/annotations data (endpoint URL)
            if "regions" in ADDITIONAL_MODULES:
                w_reg_processes[r.id]["treatments"][
                    "extracted_regions"
                ] = f"{BASE_URL}/{APP_NAME}/witness/{wid}/regions/{r.id}/json/extracted-regions"

            # 4 : Similarity data (endpoint URL)
            if "similarity" in ADDITIONAL_MODULES:
                w_reg_processes[r.id]["treatments"][
                    "similarities"
                ] = f"{BASE_URL}/{APP_NAME}/witness/{wid}/regions/{r.id}/json/similarities"

            # 5 : Vectorizations (endpoint URL)
            if "vectorization" in ADDITIONAL_MODULES:
                w_reg_processes[r.id]["treatments"][
                    "vectorizations"
                ] = f"{BASE_URL}/{APP_NAME}/witness/{wid}/regions/{r.id}/json/vectorized-images"

    return w_json | w_digits_manifs | {"regions": w_reg_processes}


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

    q_r = get_object_or_404(Regions, pk=rid)
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


### JSON ENCLOSINGS ###


def get_json_regions(request, wid, rid):
    if request.method == "GET":
        result = get_region_data(wid, rid)
        return JsonResponse(result, safe=False)


def get_json_simil(request, wid, rid):
    if request.method == "GET":
        witness = get_object_or_404(Witness, id=wid)
        if witness.is_public:
            # Partly taken from 'get_similar_images' in 'similarity/views.py'
            try:
                result = get_similarity_data(witness, rid, request.user.id)
                return JsonResponse(result, safe=False)
            except (json.JSONDecodeError, ValueError) as e:
                return JsonResponse({"error": f"Invalid data: {str(e)}"}, status=400)
            except Exception as e:
                return JsonResponse(
                    {"error": f"An error occurred: {str(e)}"}, status=500
                )
        else:
            return JsonResponse({})


def get_json_witness(request, wid):
    if request.method == "GET":
        witness = get_object_or_404(Witness, id=wid)
        if witness.is_public:
            try:
                result = get_witness_data(witness, json_cascade=True)
                return JsonResponse(result, safe=False)
            except (json.JSONDecodeError, ValueError) as e:
                return JsonResponse({"error": f"Invalid data: {str(e)}"}, status=400)
            except Exception as e:
                return JsonResponse(
                    {"error": f"An error occurred: {str(e)}"}, status=500
                )
        else:
            return JsonResponse({})


def get_json_vecto(request, wid, rid):
    if request.method == "GET":
        witness = get_object_or_404(Witness, id=wid)
        if witness.is_public:
            result = get_vecto_data(rid, include_svg=True)
            return JsonResponse(result, safe=False)
    return JsonResponse({})


def get_json_document_set(request, dsid):
    ds_data = {}
    if request.method == "GET":
        doc_set = get_object_or_404(DocumentSet, id=dsid)
        ds_data = {
            w.id: f"{BASE_URL}/{APP_NAME}/witness/{w.id}/json"
            for w in doc_set.all_witnesses()
            if w.is_public
        }
    return JsonResponse(ds_data, safe=False)
