import json
import re
from collections import OrderedDict
from typing import List, Dict, Tuple, Set, Literal

from django.db.models import Q, Count, CharField, Value
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError

from django.contrib.auth.decorators import user_passes_test

from app.similarity.const import SCORES_PATH
from app.similarity.models.region_pair import RegionPair, RegionPairTuple
from app.webapp.models.digitization import Digitization
from app.webapp.models.regions import Regions
from app.webapp.models.witness import Witness
from app.webapp.utils.functions import sort_key
from app.webapp.utils.logger import log
from app.webapp.utils.iiif import parse_ref
from app.similarity.utils import (
    send_request,
    check_computed_pairs,
    get_computed_pairs,
    get_best_pairs,
    get_region_pairs_with,
    get_regions_q_imgs,
    validate_img_ref,
    get_matched_regions,
    get_all_pairs,
    reset_similarity,
)
from app.webapp.utils.tasking import receive_notification
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
        if send_request(regions):
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
def receive_similarity_notification(request):
    """
    Handle response of the API sending back similarity files
    """
    response, status_code = receive_notification(request)
    return JsonResponse(response, status=status_code, safe=False)


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

    if not len(q_regions):
        return JsonResponse(
            {"error": f"No regions found for this witness #{wid}"}, status=400
        )

    try:
        data = json.loads(request.body.decode("utf-8"))
        regions_ids = list(data.get("regionsIds", []))
        q_img = str(data.get("qImg", ""))
        topk = min(max(int(data.get("topk", 10)), 1), 20)
        excluded_cat = list(data.get("excludedCategories", [4]))

        if not regions_ids or not q_img:
            return JsonResponse({})

        all_pairs = get_region_pairs_with(q_img, regions_ids, include_self=True)

        # Process pairs for each q_region
        result = []
        for q_r in q_regions:
            pairs = [
                pair
                for pair in all_pairs
                if pair.regions_id_1 == q_r.id or pair.regions_id_2 == q_r.id
            ]
            if q_r.id not in regions_ids:
                pairs = [
                    pair for pair in pairs if pair.regions_id_1 != pair.regions_id_2
                ]

            result.extend(
                get_best_pairs(
                    q_img,
                    pairs,
                    excluded_categories=excluded_cat,
                    topk=topk,
                    user_id=request.user.id,
                )
            )

        return JsonResponse(result, safe=False)

    except (json.JSONDecodeError, ValueError) as e:
        return JsonResponse({"error": f"Invalid data: {str(e)}"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)


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
        current_regions = {q_r.get_ref(): q_r.get_json() for q_r in q_regions}

        # Collect all region IDs to query at once
        all_region_ids = set()
        for q_r in q_regions:
            pairs = RegionPair.objects.filter(
                Q(regions_id_1=q_r.id) | Q(regions_id_2=q_r.id)
            ).values_list("regions_id_1", "regions_id_2")

            for id1, id2 in pairs:
                all_region_ids.add(id2 if id1 == q_r.id else id1)

        # Remove the original region IDs from the set
        all_region_ids -= set(q_r.id for q_r in q_regions)

        # Fetch all similar regions in one query
        sim_regions = Regions.objects.filter(id__in=all_region_ids)
        compared_regions = dict(
            sorted(
                {r.get_ref(): r.get_json() for r in sim_regions}.items(),
                key=lambda x: sort_key(x[0]),
            )
        )

        return JsonResponse(OrderedDict({**current_regions, **compared_regions}))
    except Exception as e:
        log("[get_compared_regions] Couldn't retrieve compared regions", e)
        return JsonResponse(
            {"error": f"Couldn't retrieve compared regions: {e}"}, status=400
        )


def suggested_regions_directed(img_id: str) -> List[RegionPair | None]:
    def single_call(_img_id: str, queried: List[int] = []) -> List[str | None]:
        return list(
            RegionPair.objects.distinct()
            .filter(Q(img_1=_img_id) & Q(category=1) & ~Q(id__in=queried))
            .all()
        )

    def get_queried(_propagated_matches: List[RegionPair | None]):
        return [rp.id for rp in _propagated_matches]

    def get_propagated_matches(
        _img_id: str, _propagated_matches: List[RegionPair | None] = [], depth: int = 0
    ):
        max_depth = 5
        depth += 1
        if depth > max_depth:
            return _propagated_matches
        queried_row_ids = get_queried(_propagated_matches)
        for regionpair in single_call(_img_id, queried_row_ids):
            if regionpair.id not in queried_row_ids:
                # 1st, add all newly retried rows to _propagated_matches.
                # 2nd, recursively add propagated matches, which will rerun 1st and thus populate `propagated_matches`
                _propagated_matches.append(regionpair)
                _propagated_matches = get_propagated_matches(
                    regionpair.img_2, _propagated_matches, depth
                )
        return _propagated_matches

    propagated_matches = get_propagated_matches(img_id, depth=0)

    return propagated_matches


def suggested_regions_undirected(img_id: str) -> List[RegionPair | None]:
    # TODO see if we also need to do filtering by region id (param `rid`)
    # TODO further optimize `get_propagated_matches` ? a lot of the later calls to `single_call_undirected()` return nothing, which means that they are "useless" and could be deleted in theory.
    def single_call(_img_id: str, queried: List[str] = []) -> List[RegionPair | None]:
        """
        get all exact matches related to node _img_id, non-recursively.

        equivalent to (tested manually without recursion, the
        SQL and Django ORM variants return the same n° of results):
        ```        WITH entry_point AS (SELECT $_img_id)
        SELECT *, 'img_1' AS "target"
        FROM webapp_regionpair
        WHERE
            webapp_regionpair.category=1
            AND webapp_regionpair.img_2 IS NOT IN $queried
            AND webapp_regionpair.img_2 = $_img_id
        UNION (
            SELECT *, 'img_2' AS "target"
            FROM webapp_regionpair
            WHERE
                webapp_regionpair.category=1
                AND webapp_regionpair.img_1 IS NOT IN $queried
                AND webapp_regionpair.img_1 = $_img_id
        )
        ;
        ```
        """
        img_2_from_1 = (
            RegionPair.objects.distinct()
            .filter(Q(img_1=_img_id) & Q(category=1) & ~Q(img_2__in=queried))
            .annotate(target=Value("img_2", output_field=CharField()))
        )
        img_1_from_2 = (
            RegionPair.objects.distinct()
            .filter(Q(img_2=_img_id) & Q(category=1) & ~Q(img_1__in=queried))
            .annotate(target=Value("img_1", output_field=CharField()))
        )
        return list(img_2_from_1.union(img_1_from_2).all())

    def get_queried(
        _propagated_matches: List[Tuple[RegionPair, int] | None]
    ) -> List[int]:
        queried_imgs = []
        for regionpair, depth in _propagated_matches:
            # queried_imgs.append(regionpair.img_1)
            # queried_imgs.append(regionpair.img_2)
            queried_imgs.append(regionpair.id)
        return queried_imgs

    def get_propagated_matches(
        _img_id: str, _propagated_matches: List[str | None] = [], depth: int = 0
    ) -> List[Tuple[RegionPair, int] | None]:
        """
        create the subgraph `propagated_matches`.
        1. check depth to avoid excessive recursion.
        2. get all previously queried elts in `_propagated_matches`
        3. get new matches for `_img_id`
        4. propagate: for each new image match, run `get_propagated_matches`

        :returns:
            Tuple(RegionPair, depth). we log the depth because RegionPairs
            with depth==1 will be removed later on.
        """
        max_depth = 5
        depth += 1
        if depth > max_depth:
            return _propagated_matches
        queried_imgs = get_queried(_propagated_matches)
        print(">>>>>>> _img_id", _img_id)
        print(">>>>>>> queried_imgs", queried_imgs)
        for regionpair in single_call(_img_id, queried_imgs):
            # queried = (
            #     regionpair.img_1 in queried_imgs
            #     if regionpair.target == "img_2"
            #     else regionpair.img_2 in queried_imgs
            # )
            queried = regionpair.id in queried_imgs
            if not queried:
                # 1st, add all newly retried rows to _propagated_matches
                # (we don't add depths from the 1st match to avoid displaying imgA <exactMatch> imgB in _propagated_matches).
                # 2nd, recursively add propagated matches, which will rerun 1st and thus populate `_propagated_matches`
                _propagated_matches.append((regionpair, depth))
                _propagated_matches = get_propagated_matches(
                    regionpair.img_1
                    if regionpair.target == "img_1"
                    else regionpair.img_2,
                    _propagated_matches,
                    depth,
                )
        return _propagated_matches

    propagated_matches = get_propagated_matches(img_id, depth=0)
    print(">>>>>>> propagated_matches", propagated_matches)
    print(">>>>>>> propagated_matches depth", set(d for (rp, d) in propagated_matches))
    print("*****************************************")

    # we remove matches with depth 1 since they aldready are exact matches (imgA <exactMatch> imgB)
    return [regionpair for (regionpair, depth) in propagated_matches if depth > 1]


def get_suggested_regions(request, wid: str, rid: int, img_id: str):
    """
    propagates exact matches between `img_id` and others.

    suggested regions are RegionPair entries where
    (with imgA being a value of RegionPair.img_1 or RegionPair.img_2):
    ```
    imgA <exactMatch> imgB, imgB <exactMatch> imgC, imgC <exactMatch> imgD
    => imgA <suggestedMatch> (imgB, imgD)
    ```

    in graph terms, suggested regions are an undrirected subgraph G
    - where nodes are members of (RegionPair.img_1, RegionPair.img_2)
    - where edges are relations between img_1 and img_2 in rows of
        RegionPair, where `RegionPair.category == 1` (1 = exact match)
    - where one of the nodes is `img_id`
    """

    def regions_id_from_img_id(_img_id: str, target: Literal[1, 2]) -> str:
        """
        assuming unique values of RegionPair.img_(1|2)
        can only be mapped to an unique RegionPair.regions_id_(1|2),
        retrieve the region id from the img name.
        """
        field_regions = "regions_id_1" if target == 1 else "regions_id_2"
        field_img = "img_1" if target == 1 else "img_2"
        region_id = (
            RegionPair.objects.values_list(field_regions)
            .filter(**{field_img: _img_id})
            .first()
        )
        return region_id[0] if region_id else None

    source_regions_id = regions_id_from_img_id(img_id, 1)

    # propagated_matches = suggested_regions_directed(img_id)
    propagated_matches = suggested_regions_undirected(img_id)

    # so far, `propagated_matches` does not store relations between
    # `imgA` and `imgD` (query image and matched image), but between
    # `ìmgC` and `imgD` (an intermediary matched image and the final
    # suggested match) => create RegionPairs between `ìmgA` and `ìmgD`
    # (those RegionPairs are not saved into the DB and only used to build
    # a JSON for the front)
    to_regionpair_info = lambda _img_1, _regions_id_1, regionpair: (
        RegionPair(
            score=None,  # no actual match was made, so no score.
            img_1=_img_1,
            img_2=regionpair.img_1
            if regionpair.target == "img_1"
            else regionpair.img_2,
            regions_id_1=_regions_id_1,
            regions_id_2=regionpair.regions_id_1
            if regionpair.target == "img_1"
            else regionpair.regions_id_2,
        ).get_info()
    )
    propagated_matches_json = [
        to_regionpair_info(img_id, source_regions_id, rp) for rp in propagated_matches
    ]
    return JsonResponse(propagated_matches_json, safe=False)


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
        return regions.id

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


def add_region_pair(
    request, wid, rid=None, context: Literal["default", "suggestion"] = "default"
) -> Tuple[Dict, int]:
    """
    :returns:
        status: html status code
        response: json to send to the frontend
    """
    if request.method != "POST":
        return {"error": "Invalid request method"}, 400

    try:
        data = json.loads(request.body)
        q_img, s_img = data.get("q_img"), data.get("s_img")

        if not (validate_img_ref(q_img) and validate_img_ref(s_img)):
            raise ValidationError("Invalid image string format")

        img_1, img_2 = sorted([q_img, s_img], key=sort_key)
        regions_1, regions_2 = get_regions(img_1, img_2, wid, rid)

        if context == "default":
            defaults = {
                "regions_id_1": regions_1,
                "regions_id_2": regions_2,
                "is_manual": True,
            }
        else:
            category = data.get("category")
            category_x = data.get("category_x")
            defaults = {
                "regions_id_1": regions_1,
                "regions_id_2": regions_2,
                "category": category,
                "category_x": category_x,
                "is_manual": False,
                "score": 0,  # TBDDDDDDDDDDDD???????
            }

        region_pair, created = RegionPair.objects.get_or_create(
            img_1=f"{img_1}.jpg",
            img_2=f"{img_2}.jpg",
            defaults=defaults,
        )

        # in theory, it is not triggered if context=="suggestions"
        if not created:
            if region_pair.category_x is None:
                region_pair.category_x = [request.user.id]
            elif request.user.id not in region_pair.category_x:
                region_pair.category_x.append(request.user.id)
            region_pair.save()

        s_regions = get_object_or_404(
            Regions, id=regions_2 if q_img == img_1 else regions_1
        )
        return {
            "success": "Region pair added successfully",
            "s_regions": s_regions.get_json(),
            "created": created,
        }

    except json.JSONDecodeError:
        return {"error": "Invalid JSON data"}, 400
    except ValidationError as e:
        return {"error": str(e)}, 400
    except Exception as e:
        return {"error": f"An error occurred: {e}"}, 500


def add_region_pair_default(request, wid, rid=None):
    """
    generally used for adding manual matches
    """
    response, status = add_region_pair(request, wid, rid, "default")
    return JsonResponse(response, status=status)


def add_region_pair_suggested_regions(request, wid, rid=None):
    """
    used when validating a suggested regionpair (see `get_suggested_regions`)

    TODO: FRONTEND IMPLEMENTATION.
    """
    response, status = add_region_pair(request, wid, rid, "default")
    return JsonResponse(response, status=status)


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
            # NOTE remove pair once and for all?
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
            rid = q_r.id
            q_imgs.update(get_regions_q_imgs(q_r.id, wid))
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
        category_x = data.get("category_x")

        region_pair, created = RegionPair.objects.get_or_create(
            img_1=img_1,
            img_2=img_2,
        )

        region_pair.category = int(category) if category else None
        region_pair.category_x = sorted(category_x)
        region_pair.save()

        if created:
            # Shouldn't happen since all displayed regions are retrieved from database
            return JsonResponse(
                {"status": "success", "message": "New region pair created"}, status=200
            )
        return JsonResponse(
            {"status": "success", "message": "Existing region pair updated"}, status=200
        )


@user_passes_test(is_superuser)
def index_regions_similarity(request, regions_ref=None):
    """
    Index the content of a scores npy files containing regions_ref in their name
    OR all the similarity score files into the RegionPair database table
    if the score files have already been added to the database, it will only override the score
    """
    from app.similarity.tasks import process_similarity_file

    if regions_ref is None:
        pairs = get_all_pairs()
    else:
        pairs = get_computed_pairs(regions_ref)

    for pair in pairs:
        process_similarity_file.delay(pair)

    return JsonResponse(
        {
            "Launched": pairs,
        }
    )


@user_passes_test(is_superuser)
def delete_all_regions_pairs(request):
    # NOTE deactivated, only for dev purposes
    all_regions = Regions.objects.all()
    reset_similarities = []
    for regions in all_regions:
        if reset_similarity(regions):
            reset_similarities.append(regions.id)
    return JsonResponse(
        {
            "message": f"Regions {', '.join(map(str, reset_similarities))} have been reset"
        }
    )


def reset_regions_similarity(request, rid=None):
    if request.method == "DELETE":
        if rid:
            regions = get_object_or_404(Regions, id=rid)
            if reset_similarity(regions):
                return JsonResponse(
                    {"message": f"Regions #{rid} similarities has been reset"}
                )
            return JsonResponse(
                {"error": f"Regions #{rid} similarities couldn't been reset"},
                status=400,
            )

        return JsonResponse({"error": f"No region id provided"}, status=400)
    return JsonResponse({"error": f"Invalid request method"}, status=400)


@user_passes_test(is_superuser)
def remove_incorrect_pairs(request, mismatched=False, duplicate=False, swapped=True):
    """
    Removes RegionPair instances that are faulty
    """
    from django.db import DatabaseError

    count = 0

    try:
        if mismatched:
            from django.db.models import F

            # if img_1 is alphabetically after img_2,
            # indicating that the pair has been incorrectly inserted in the database
            mismatched_pairs = RegionPair.objects.filter(img_1__gt=F("img_2"))
            count += mismatched_pairs.count()
            mismatched_pairs.delete()

        if duplicate:
            # if there is duplicates of the same img pair with different ids
            duplicate_pairs = (
                RegionPair.objects.values("img_1", "img_2")
                .annotate(count=Count("id"))
                .filter(count__gt=1)
            )
            count += len(duplicate_pairs)
            for pair in duplicate_pairs:
                duplicates = RegionPair.objects.filter(
                    img_1=pair["img_1"], img_2=pair["img_2"]
                )
                count += duplicates.count() - 1
                duplicates[1:].delete()

        if swapped:
            # if there is duplicates of the same img pair but with img_1 and img_2 swapped
            swapped_pairs = RegionPair.objects.filter(
                Q(img_1__in=RegionPair.objects.values("img_2"))
                & Q(img_2__in=RegionPair.objects.values("img_1"))
            )
            count += len(swapped_pairs)
            for pair in swapped_pairs:
                reverse_pair = RegionPair.objects.filter(
                    img_1=pair.img_2, img_2=pair.img_1
                ).first()
                if reverse_pair:
                    sorted_imgs = sorted([pair.img_1, pair.img_2], key=sort_key)
                    if pair.img_1 != sorted_imgs[0]:
                        pair.delete()
                    else:
                        reverse_pair.delete()

        return JsonResponse({"message": f"{count} incorrect pairs removed"})

    except DatabaseError as e:
        return JsonResponse(
            {"message": f"An error occurred while removing incorrect pairs: {e}"},
            status=500,
        )
