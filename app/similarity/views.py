import json

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_GET

from app.config.settings import APP_LANG
from app.similarity.const import SCORES_PATH
from app.similarity.models.region_pair import RegionPair
from app.webapp.models.regions import Regions
from app.webapp.models.witness import Witness
from app.webapp.utils.functions import sort_key
from app.webapp.utils.logger import log
from app.similarity.utils import (
    similarity_request,
    check_score_files,
    check_computed_pairs,
    get_compared_regions_refs,
    compute_page_scores,
    get_imgs_in_score_files,
)
from app.webapp.views import is_superuser, check_ref


@user_passes_test(is_superuser)
def send_similarity(request, regions_refs):
    """
    To relaunch similarity request in case the automatic process has failed
    """

    regions = [
        region
        for (passed, region) in [check_ref(ref, "Regions") for ref in regions_refs]
        if passed
    ]

    if not len(regions):
        return JsonResponse(
            {
                "response": f"No corresponding regions in the database for {regions_refs}"
            },
            safe=False,
        )

    if len(check_computed_pairs(regions_refs)) == 0:
        return JsonResponse(
            {"response": f"All similarity pairs were computed for {regions_refs}"},
            safe=False,
        )

    try:
        if similarity_request(regions):
            return JsonResponse(
                {"response": f"Successful similarity request for {regions_refs}"},
                safe=False,
            )
        return JsonResponse(
            {"response": f"Failed to send similarity request for {regions_refs}"},
            safe=False,
        )

    except Exception as e:
        error = f"[send_similarity] Couldn't send request for {regions_refs}"
        log(error, e)

        return JsonResponse({"response": error, "reason": e}, safe=False)


@csrf_exempt
def receive_similarity(request):
    """
    Handle response of the API sending back similarity files
    """
    if request.method == "POST":
        filenames = []
        try:
            for regions_refs, file in request.FILES.items():
                with open(f"{SCORES_PATH}/{regions_refs}.npy", "wb") as destination:
                    filenames.append(regions_refs)
                    for chunk in file.chunks():
                        destination.write(chunk)

            check_score_files(filenames)
            return JsonResponse({"message": "Score files received successfully"})
        except Exception as e:
            log("[receive_similarity] Error saving score files", e)
            return JsonResponse({"message": "Error saving score files"}, status=500)
    return JsonResponse({"message": "Invalid request"}, status=400)


def compute_score(request):
    # NOTE could become irrelevant very soon
    from app.similarity.tasks import compute_similarity_scores

    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            regions_refs = data.get("regionsRefs", [])
            max_rows = int(data.get("maxRows", 50))
            show_checked_ref = data.get("showCheckedRef", True)
            if len(regions_refs) == 0:
                return JsonResponse(
                    {"error": "No regions_ref to retrieve score"}, status=400
                )
            # TODO here does not use delayed task
            return JsonResponse(
                compute_similarity_scores(regions_refs, max_rows, show_checked_ref),
                status=200,
            )
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=400)


def get_similarity_page(request, wid, rid=None):
    if request.method == "POST":
        if rid is not None:
            q_regions = [get_object_or_404(Regions, id=rid)]
        else:
            witness = get_object_or_404(Witness, id=wid)
            q_regions = witness.get_regions()

        try:
            data = json.loads(request.body.decode("utf-8"))
            regions_ids = data.get("regionsIds", [])
            page_imgs = data.get("pageImgs", [])

            if len(regions_ids) == 0:
                # selection is empty
                return JsonResponse({})

            page_scores = {}
            for q_r in q_regions:
                include_q_doc = q_r.id in regions_ids
                sim_regions = [
                    Regions.objects.get(id=region_id) for region_id in regions_ids
                ]
                page_scores.update(
                    compute_page_scores(
                        q_r, sim_regions, include_q_doc, page_q_imgs=page_imgs
                    )
                )

            return JsonResponse(page_scores)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=400)


def get_similar_regions(request, wid, rid=None):
    """
    Return the id and metadata of the Regions that have a score file of similarity
    in common with the Regions whose id is passed in the URL
    """
    if rid is not None:
        q_regions = [get_object_or_404(Regions, id=rid)]
    else:
        witness = get_object_or_404(Witness, id=wid)
        q_regions = witness.get_regions()

    try:
        sim_regions = []
        for q_r in q_regions:
            q_ref = q_r.get_ref()
            sim_refs = get_compared_regions_refs(q_ref)
            sim_regions += [
                region
                for (passed, region) in [check_ref(ref, "Regions") for ref in sim_refs]
                if passed
            ]
        return JsonResponse({r.get_ref(): r.to_json() for r in sim_regions})
    except Exception as e:
        return JsonResponse(
            {"error": f"Couldn't retrieve compared regions: {e}"}, status=400
        )


def get_query_images(request, wid, rid=None):
    if request.method == "POST":
        if rid is not None:
            q_regions = [get_object_or_404(Regions, id=rid)]
        else:
            witness = get_object_or_404(Witness, id=wid)
            q_regions = witness.get_regions()

        try:
            q_imgs = set()
            for q_r in q_regions:
                q_ref = q_r.get_ref()
                data = json.loads(request.body.decode("utf-8"))
                sim_refs = data.get("regionsRefs", [])
                pairs = ["-".join(sorted((q_ref, sim_ref))) for sim_ref in sim_refs]
                q_prefix = "_".join(q_ref.split("_")[:2])
                q_imgs.update(get_imgs_in_score_files(pairs, q_prefix))
            return JsonResponse(sorted(list(q_imgs)), safe=False)
        except Exception as e:
            return JsonResponse(
                {
                    "error": f"Couldn't retrieve images of regions #{rid} in score files: {e}"
                },
                status=400,
            )

    return JsonResponse({"error": "Invalid request method"}, status=400)


def show_similarity(request, regions_ref):
    refs = get_compared_regions_refs(regions_ref)
    regions = {
        region.get_ref(): region.__str__()
        for (passed, region) in [check_ref(ref, "Regions") for ref in refs]
        if passed
    }

    return render(
        request,
        "show_similarity.html",
        context={
            "title": "Similarity search result"
            if APP_LANG == "en"
            else "Résultat de recherche de similarité",
            "regions": dict(sorted(regions.items())),
            "checked_ref": regions_ref,
            "checked_ref_title": regions[regions_ref],
            "regions_refs": json.dumps(refs),
        },
    )


@require_GET
def retrieve_category(request):
    img_1, img_2 = sorted(
        [request.GET.get("img_1"), request.GET.get("img_2")], key=sort_key
    )

    try:
        region_pair = RegionPair.objects.get(img_1=img_1, img_2=img_2)
        category = region_pair.category
        category_x = region_pair.category_x
    except RegionPair.DoesNotExist:
        category = None
        category_x = []

    return JsonResponse({"category": category, "category_x": category_x})


@csrf_exempt
def save_category(request):
    if request.method == "POST":
        data = json.loads(request.body)
        img_1, img_2 = sorted([data.get("img_1"), data.get("img_2")], key=sort_key)
        regions_ref_1, regions_ref_2 = sorted(
            [data.get("regions_ref_1"), data.get("regions_ref_2")], key=sort_key
        )
        category = data.get("category")
        category_x = data.get("category_x")
        user_id = request.user.id

        region_pair, created = RegionPair.objects.get_or_create(
            img_1=img_1,
            img_2=img_2,
            defaults={
                "regions_ref_1": regions_ref_1,
                "regions_ref_2": regions_ref_2,
            },
        )

        region_pair.category = int(category) if category else None

        # If the user's id doesn't exist in category_x, append it
        if category_x is not None:
            if user_id not in region_pair.category_x:
                region_pair.category_x.append(user_id)
            region_pair.category_x = sorted(region_pair.category_x)
        else:  # If category_x is None, remove the user's id if it exists
            if user_id in region_pair.category_x:
                region_pair.category_x.remove(user_id)

        region_pair.save()

        if created:
            return JsonResponse(
                {"status": "success", "message": "New region pair created"}, status=200
            )
        return JsonResponse(
            {"status": "success", "message": "Existing region pair updated"}, status=200
        )
