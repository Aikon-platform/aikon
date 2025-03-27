import json
from pathlib import Path

from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import cache_page
from django.db.models import F

from app.config.settings import APP_URL, APP_NAME
from app.webapp.models.digitization import Digitization
from app.webapp.models.document_set import DocumentSet
from app.webapp.models.regions import Regions
from app.webapp.models.witness import Witness
from app.webapp.utils.constants import MANIFEST_V2, PAGE_LEN
from app.webapp.utils.functions import (
    zip_img,
    get_files_in_dir,
    get_files_with_prefix,
)
from app.webapp.utils.iiif import gen_iiif_url
from app.webapp.utils.iiif.annotation import (
    get_regions_annotations,
)
from app.webapp.utils.logger import log
from app.webapp.utils.paths import MEDIA_DIR
from app.webapp.utils.regions import create_empty_regions
from app.webapp.tasks import generate_all_json
from webapp.utils.paths import REGIONS_PATH
from webapp.utils.tasking import create_doc_set

from app.similarity.utils import (
    get_best_pairs,
    get_region_pairs_with,
    get_compared_regions_ids,
    get_regions_q_imgs,
)
from app.vectorization.const import SVG_PATH

"""
VIEWS THAT SERVE AS ENDPOINTS
ONLY FOR API CALLS
"""


def json_regeneration(request):
    task = generate_all_json.delay()
    return JsonResponse(
        {"message": "JSON regeneration task started", "task_id": str(task.id)}
    )


def save_document_set(request, dsid=None):
    """
    Endpoint used to create/update a document set
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))

            selection = data.get("selection", [])
            set_name = data.get("title", None)
            witness_ids = data.get("Witness", [])
            series_ids = data.get("Series", [])
            work_ids = data.get("Work", [])

            if len(witness_ids) + len(series_ids) + len(work_ids) == 0:
                return JsonResponse(
                    {"error": "No documents to save in the set"}, status=400
                )

            try:
                keep_title = False
                if dsid:
                    ds = DocumentSet.objects.get(id=dsid)
                    ds.wit_ids = witness_ids
                    ds.ser_ids = series_ids
                    ds.work_ids = work_ids
                else:
                    ds, is_new = create_doc_set(
                        {
                            "wit_ids": witness_ids,
                            "ser_ids": series_ids,
                            "work_ids": work_ids,
                        },
                        user=request.user,
                    )
                    keep_title = not is_new

                ds.selection = selection
                title = ds.title if keep_title else set_name
                ds.title = f"{title} #{ds.id}" if "#" not in title else title
                ds.save()

            except Exception as e:
                return JsonResponse(
                    {"error": f"Failed to save document set: {e}"}, status=500
                )
            return JsonResponse(
                {
                    "message": "Document set saved successfully",
                    "document_set_id": ds.id,
                    "document_set_title": ds.title,
                }
            )
        except Exception as e:
            return JsonResponse(
                {"message": f"Error saving score files: {e}"}, status=500
            )
    return JsonResponse({"message": "Invalid request"}, status=400)


def get_canvas_regions(request, wid, rid):
    # TODO mutualize with get_canvas_witness_regions
    regions = get_object_or_404(Regions, id=rid)
    p_nb = int(request.GET.get("p", 0))
    max_canvas = regions.get_json()["img_nb"]
    if p_nb > 0:
        p_len = PAGE_LEN
        max_c = p_nb * p_len
        min_c = max_c - p_len
        return JsonResponse(
            get_regions_annotations(
                regions,
                as_json=True,
                r_annos={},
                min_c=min_c,
                max_c=min(max_c, max_canvas),
            ),
            safe=False,
        )
    # to retrieve all regions
    return JsonResponse(
        get_regions_annotations(regions, as_json=True, min_c=1, max_c=max_canvas),
        safe=False,
    )


def get_canvas_witness_regions(request, wid):
    witness = get_object_or_404(Witness, id=wid)
    p_nb = int(request.GET.get("p", 0))
    anno_regions = {}
    if p_nb > 0:
        p_len = PAGE_LEN
        max_c = p_nb * p_len
        min_c = max_c - p_len
        for regions in witness.get_regions():
            max_canvas = regions.get_json()["img_nb"]
            anno_regions = get_regions_annotations(
                regions,
                as_json=True,
                r_annos=anno_regions,
                min_c=min_c,
                max_c=min(max_c, max_canvas),
            )
    else:
        # to retrieve all regions
        for regions in witness.get_regions():
            max_c = regions.get_json()["img_nb"]
            anno_regions = get_regions_annotations(
                regions, as_json=True, r_annos=anno_regions, min_c=1, max_c=max_c
            )

    return JsonResponse(anno_regions, safe=False)


def create_manual_regions(request, wid, did=None, rid=None):
    if request.method == "POST":
        if rid:
            regions = get_object_or_404(Regions, id=rid)
            return JsonResponse(
                {
                    "regions_id": regions.id,
                    "mirador_url": regions.gen_mirador_url(),
                },
            )

        witness = get_object_or_404(Witness, id=wid)
        digit = None
        if did:
            digit = get_object_or_404(Digitization, id=did)
        else:
            for d in witness.get_digits():
                if d.has_images():
                    digit = d
                    break

        if not digit:
            return JsonResponse(
                {"error": "No digitization available for this witness"}, status=500
            )

        regions = create_empty_regions(digit)
        if not regions:
            return JsonResponse({"error": "Unable to create regions"}, status=500)
        return JsonResponse(
            {
                "regions_id": regions.id,
                "mirador_url": regions.gen_mirador_url(),
            },
        )
    return JsonResponse({"error": "Invalid request method"}, status=400)


def delete_regions(request, rid):
    from app.webapp.tasks import delete_annotations
    from app.regions.tasks import delete_api_regions

    if request.method == "DELETE":
        regions = get_object_or_404(Regions, id=rid)
        try:
            delete_annotations.delay(
                regions.get_ref(), regions.gen_manifest_url(version=MANIFEST_V2)
            )

            Path(f"{REGIONS_PATH}/{regions.get_ref()}.json").unlink(missing_ok=True)

            delete_api_regions.delay(regions.get_digit().get_ref(), regions.model)

            try:
                # Delete the regions record in the database
                regions.delete()
            except Exception as e:
                return JsonResponse(
                    {"message": f"Failed to delete regions record #{rid}: {e}"},
                    status=400,
                )

            return JsonResponse({"message": "Regions deletion requested"}, status=204)
        except Exception as e:
            log(f"[delete_regions] Error sending deletion task for regions #{rid}", e)
            return JsonResponse(
                {"error": f" Error sending deletion task for regions #{rid}: {e}"},
                status=500,
            )
    return JsonResponse({"error": "Invalid request method"}, status=400)


def export_regions(request):
    if request.method == "POST":
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


# DIRTY FIX FOR SAS 😡
@cache_page(60 * 60 * 24)  # Cache for 24h
def iiif_context(request):
    try:
        context_path = Path(MEDIA_DIR) / "context.json"
        if not context_path.exists():
            import requests

            response = requests.get("http://iiif.io/api/presentation/2/context.json")
            context_data = response.json()
            with open(context_path, "w") as f:
                json.dump(context_data, f)
        else:
            with open(context_path, "r") as f:
                context_data = json.load(f)

        return JsonResponse(
            context_data,
            content_type="application/json",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            },
        )

    except Exception as e:
        return JsonResponse({"error": f"Unable to load IIIF context: {e}"}, status=500)

def get_json_witness(request, wid):
    if request.method == "GET":
        witness = get_object_or_404(Witness, id=wid)

        # 1 : JSON descriptif existant
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

        # 2 : Digitizations (sous forme de manifests)
        w_digits_ids = witness.get_digits()
        test = Digitization.objects.filter(id__in=w_digits_ids)
        test1 = Digitization.objects.filter(id__in=w_digits_ids).values_list(
            "id", "manifest"
        )
        test2 = Digitization.objects.filter(id__in=w_digits_ids).values()
        w_digits_manifs = {
            "digitizations": dict(
                Digitization.objects.filter(id__in=w_digits_ids)
                .annotate(manifest_json=F("json__url"))
                .values_list("id", "manifest_json")
            )
        }

        w_processes = {"extracted_regions": {}, "vectorizations": {}}
        # 3 : Régions (URL d'endpoint)
        w_processes[
            "extracted_regions"
        ] = f"{APP_URL}/{APP_NAME}/witness/{wid}/json/regions"

        # 4 : Similarités (URL d'endpoint)
        w_processes[
            "similarities"
        ] = f"{APP_URL}/{APP_NAME}/witness/{wid}/json/similarities"

        # 5 : Vectorisations (URL d'endpoint existant)
        w_processes[
            "vectorizations"
        ] = f"{APP_URL}/{APP_NAME}/witness/{wid}/json/vectorized-images"

        return JsonResponse(
            w_json | w_digits_manifs | {"treatments": w_processes}, safe=False
        )


def get_json_regions(request, wid):
    if request.method == "GET":
        witness = get_object_or_404(Witness, id=wid)
        w_regions = witness.get_regions()
        result = {}
        try:
            for r in w_regions:
                imgs = set()
                imgs.update(get_regions_q_imgs(r.id, wid))
                result[r.id] = {
                    "manifest": get_object_or_404(Regions, pk=r.id).gen_manifest_url(),
                    "iiif_crops": list(imgs),
                }

            return JsonResponse(result, safe=False)

        except (json.JSONDecodeError, ValueError) as e:
            return JsonResponse({"error": f"Invalid data: {str(e)}"}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)


def get_json_simil(request, wid):
    if request.method == "GET":
        witness = get_object_or_404(Witness, id=wid)
        q_regions = witness.get_regions()

        if not len(q_regions):
            return JsonResponse(
                {"error": f"No regions found for this witness #{wid}"}, status=400
            )

        # Inspiré de get_similar_views dans similarity/views.py
        try:
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
            for q_r in q_regions:
                q_imgs_set.update(get_regions_q_imgs(q_r.id, wid))

            q_imgs = sorted(list(q_imgs_set))

            regions_ids = []
            for q_r in q_regions:
                regions_ids += get_compared_regions_ids(q_r.id)

            result = {}
            for q_img in q_imgs:
                if not regions_ids or not q_img:
                    return JsonResponse({})

                all_pairs = get_region_pairs_with(q_img, regions_ids, include_self=True)

                # Process pairs for each q_region
                result[q_img] = []
                for q_r in q_regions:
                    pairs = [
                        pair
                        for pair in all_pairs
                        if pair.regions_id_1 == q_r.id or pair.regions_id_2 == q_r.id
                    ]
                    if q_r.id not in regions_ids:
                        pairs = [
                            pair
                            for pair in pairs
                            if pair.regions_id_1 != pair.regions_id_2
                        ]

                    best_pairs = get_best_pairs(
                        q_img,
                        pairs,
                        excluded_categories=[],
                        topk=-1,
                        user_id=request.user.id,
                    )
                    dict_pairs = [dict((zip(keys, p))) for p in best_pairs]
                    result[q_img].extend(dict_pairs)

            return JsonResponse(result, safe=False)

        except (json.JSONDecodeError, ValueError) as e:
            return JsonResponse({"error": f"Invalid data: {str(e)}"}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)


def get_json_vecto(request, wid):
    if request.method == "GET":
        # repris de get_vectorized_images dans vectorization/views.py
        witness = get_object_or_404(Witness, id=wid)
        q_regions = witness.get_regions()
        v_imgs = {}
        for q_r in q_regions:
            try:
                r_ref = q_r.get_ref()
                v_imgs[q_r.id] = []

                for file in get_files_in_dir(f"{SVG_PATH}/{r_ref}"):
                    file_path = f"{SVG_PATH}/{r_ref}/{file}"
                    print(file_path)
                    with open(file_path, "r", encoding="utf-8") as f:
                        v_imgs[q_r.id].append(
                            {"filename": f"{r_ref}/{file}", "svg": f.read()}
                        )

            except ValueError:
                digit_ref = q_r.get_ref().split("_anno")[0]
                v_imgs[q_r.id] = []
                for file_path in get_files_with_prefix(SVG_PATH, digit_ref):
                    print(file_path)
                    with open(file_path, "r", encoding="utf-8") as f:
                        v_imgs[q_r.id].append({"filename": file_path, "svg": f.read()})
            # try:
            #     r_ref = q_r.get_ref()
            #     v_imgs[q_r.id] = set()
            #     v_imgs[q_r.id].update(
            #         f"{r_ref}{file}" for file in get_files_in_dir(f"{SVG_PATH}/{r_ref}")
            #     )
            # except ValueError:
            #     digit_ref = q_r.get_ref().split("_anno")[0]
            #     v_imgs[q_r.id].update(get_files_with_prefix(SVG_PATH, digit_ref))
            # v_imgs[q_r.id] = list(v_imgs[q_r.id])

        return JsonResponse(v_imgs, safe=False)


def get_json_document_set(request, dsid):
    if request.method == "GET":
        doc_set = get_object_or_404(DocumentSet, id=dsid)
        ds_data = {
            w.id: f"{APP_URL}/{APP_NAME}/witness/{w.id}/json"
            for w in doc_set.all_witnesses()
        }
        return JsonResponse(ds_data, safe=False)
