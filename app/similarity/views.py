import json
import re

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError

from django.contrib.auth.decorators import login_required, user_passes_test

from app.config.settings import APP_LANG
from app.similarity.const import SCORES_PATH
from app.similarity.models.region_pair import RegionPair
from app.webapp.models.digitization import Digitization
from app.webapp.models.regions import Regions
from app.webapp.models.witness import Witness
from app.webapp.utils.functions import sort_key
from app.webapp.utils.logger import log
from app.similarity.utils import (
    similarity_request,
    check_computed_pairs,
    get_computed_pairs,
    get_best_pairs,
    get_region_pairs_with,
    get_compared_regions_ids,
    get_regions_q_imgs,
    validate_img_ref,
    get_matched_regions,
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
    from app.similarity.tasks import process_similarity_file

    if request.method == "POST":
        filenames = []
        try:
            for regions_refs, file in request.FILES.items():
                with open(f"{SCORES_PATH}/{regions_refs}.npy", "wb") as destination:
                    filenames.append(regions_refs)
                    for chunk in file.chunks():
                        destination.write(chunk)
                process_similarity_file.delay(f"{SCORES_PATH}/{regions_refs}.npy")

            return JsonResponse({"message": "Score files received successfully"})
        except Exception as e:
            log("[receive_similarity] Error saving score files", e)
            return JsonResponse({"message": "Error saving score files"}, status=500)

    return JsonResponse({"message": "Invalid request"}, status=400)


@user_passes_test(is_superuser)
def delete_all_regions_pairs(request):
    # NOTE deactivated, only for dev purposes
    RegionPair.objects.all().delete()
    return JsonResponse({"message": "All region pairs deleted"})


@user_passes_test(is_superuser)
def index_regions_similarity(request, regions_ref=None):
    """
    Index the content of a scores npy files containing regions_ref in their name
    into the RegionPair database table
    if the score files have already been added to the database, it will only override the score
    """
    from app.similarity.tasks import process_similarity_file

    pairs = get_computed_pairs(regions_ref)

    for pair in pairs:
        process_similarity_file.delay(f"{SCORES_PATH}/{pair}.npy")

    return JsonResponse(
        {
            "Launched": pairs,
        }
    )


def get_similar_images(request, wid, rid=None):
    """
    Return the best region images that are similar to the query region image
    whose id is passed in the POST parameters
    """
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    if rid is not None:
        q_regions = [get_object_or_404(Regions, id=rid)]
    else:
        witness = get_object_or_404(Witness, id=wid)
        q_regions = witness.get_regions()

    try:
        data = json.loads(request.body.decode("utf-8"))
        try:
            regions_ids = list(data.get("regionsIds", []))
            q_img = str(data.get("qImg", ""))
            topk = int(data.get("topk", 10))
            excluded_cat = list(data.get("excludedCategories", [4]))
        except ValueError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

        if len(regions_ids) == 0:
            # selection is empty
            return JsonResponse({})

        if q_img == "":
            # no images to display
            return JsonResponse({})

        topk = min(max(topk, 1), 20)

        pairs = []
        for q_r in q_regions:
            pairs += get_region_pairs_with(
                q_img, regions_ids, include_self=q_r.id in regions_ids
            )

        return JsonResponse(
            get_best_pairs(
                q_img,
                pairs,
                excluded_categories=excluded_cat,
                topk=topk,
                user_id=request.user.id,
            ),
            safe=False,
        )
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)


def get_compared_regions(request, wid, rid=None):
    """
    Return the id and metadata of the Regions that have a RegionPair record
    in common with the Regions whose id is passed in the URL
    """
    if rid is not None:
        q_regions = [get_object_or_404(Regions, id=rid)]
    else:
        witness = get_object_or_404(Witness, id=wid)
        q_regions = witness.get_regions()

    try:
        sim_regions = []
        compared_regions = {}
        for q_r in q_regions:
            q_ref = q_r.get_ref()
            compared_regions[q_ref] = q_r.to_json()
            region_ids = get_compared_regions_ids(q_r.id)
            sim_regions = list(Regions.objects.filter(id__in=region_ids))
        compared_regions.update({r.get_ref(): r.to_json() for r in sim_regions})
        return JsonResponse(compared_regions)
    except Exception as e:
        return JsonResponse(
            {"error": f"Couldn't retrieve compared regions: {e}"}, status=400
        )


def get_regions(img_1, img_2, wid, rid):
    def get_digit_id(img):
        return int(re.findall(r"\d+", img)[1])

    def get_regions_from_digit(digit_id):
        digit = get_object_or_404(Digitization, id=digit_id)
        regions = list(digit.get_regions())
        if not regions:
            regions = Regions.objects.create(
                digitization=digit,
                model="manual",
            )
        else:
            regions = regions[0]
        return regions.id  # Return the id directly, not regions[0].id

    if img_1.startswith(f"wit{wid}"):
        witness = get_object_or_404(Witness, id=wid)
        regions_1 = rid or witness.get_regions()[0].id
        digit_2 = get_digit_id(img_2)
        regions_2 = get_regions_from_digit(digit_2)
    else:
        digit_1 = get_digit_id(img_1)
        regions_1 = get_regions_from_digit(digit_1)
        witness = get_object_or_404(Witness, id=wid)
        regions_2 = rid or witness.get_regions()[0].id

    return regions_1, regions_2


def add_region_pair(request, wid, rid=None):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    try:
        data = json.loads(request.body)
        q_img, s_img = data.get("q_img"), data.get("s_img")

        if not (validate_img_ref(q_img) and validate_img_ref(s_img)):
            raise ValidationError("Invalid image string format")

        img_1, img_2 = sorted([q_img, s_img], key=sort_key)

        regions_1, regions_2 = get_regions(img_1, img_2, wid, rid)

        region_pair, created = RegionPair.objects.get_or_create(
            img_1=f"{img_1}.jpg",
            img_2=f"{img_2}.jpg",
            defaults={
                # if the pair doesn't exist, create it with those values
                "regions_id_1": regions_1,
                "regions_id_2": regions_2,
                "is_manual": True,
            },
        )

        if not created:
            if request.user.id not in region_pair.category_x:
                region_pair.category_x.append(request.user.id)
                region_pair.save()

        s_regions = get_object_or_404(
            Regions, id=regions_2 if q_img == img_1 else regions_1
        )
        return JsonResponse(
            {
                "success": "Region pair added successfully",
                "s_regions": s_regions.to_json(),
                "created": created,
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except ValidationError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"An error occurred: {e}"}, status=500)


def no_match(request, wid, rid=None):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    try:
        data = json.loads(request.body)
        q_img = data.get("q_img")
        s_regions = data.get("s_regions")
        pairs = get_matched_regions(q_img, s_regions)
        for pair in pairs:
            pair.category = 4
            # TODO remove pair once and for all?
            pair.save()

        return JsonResponse({"success": "Updated matches"})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"An error occurred: {e}"}, status=500)


def get_query_images(request, wid, rid=None):
    """
    returns the list of region images associated to a query Regions
    """
    if rid is not None:
        q_regions = [get_object_or_404(Regions, id=rid)]
    else:
        witness = get_object_or_404(Witness, id=wid)
        q_regions = witness.get_regions()

    try:
        q_imgs = set()
        for q_r in q_regions:
            q_imgs.update(get_regions_q_imgs(q_r.id))
        return JsonResponse(sorted(list(q_imgs)), safe=False)
    except Exception as e:
        return JsonResponse(
            {
                "error": f"Couldn't retrieve images of regions #{rid} in the database: {e}"
            },
            status=400,
        )


def save_category(request):
    if request.method == "POST":
        data = json.loads(request.body)
        img_1, img_2 = sorted([data.get("img_1"), data.get("img_2")], key=sort_key)
        category = data.get("category")
        user_selected = data.get("user_selected")
        user_id = request.user.id

        region_pair, created = RegionPair.objects.get_or_create(
            img_1=img_1,
            img_2=img_2,
        )

        region_pair.category = int(category) if category else None
        user_category = region_pair.category_x or []

        # If the user's id doesn't exist in category_x, append it
        if user_selected:
            if user_id not in user_category:
                user_category.append(user_id)
            region_pair.category_x = sorted(user_category)
        else:  # If user_selected is False, remove the user's id if it exists
            if user_id in user_category:
                region_pair.category_x.remove(user_id)

        region_pair.save()

        if created:
            # Shouldn't happen since all displayed regions are retrieved from database
            return JsonResponse(
                {"status": "success", "message": "New region pair created"}, status=200
            )
        return JsonResponse(
            {"status": "success", "message": "Existing region pair updated"}, status=200
        )
