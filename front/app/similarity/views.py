import json
from collections import OrderedDict
from typing import List, Tuple, Set

from django.db.models import Q, Count
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError

from django.contrib.auth.decorators import user_passes_test

from app.similarity.models.region_pair import RegionPair, RegionPairTuple
from app.webapp.models.regions import Regions
from app.webapp.models.witness import Witness
from app.webapp.utils.functions import sort_key, truncate_char
from app.webapp.utils.logger import log
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
    regions_from_img,
)
from app.webapp.utils.tasking import receive_notification
from app.webapp.views import is_superuser, check_ref
from similarity.utils import add_user_to_category_x


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
        q_regions_ids = [q_r.id for q_r in q_regions]
        t_regions_ids = list(data.get("regionsIds", []))
        q_img = str(data.get("qImg", ""))
        topk = min(max(int(data.get("topk", 10)), 1), 20)

        if not t_regions_ids or not q_img:
            return JsonResponse({})

        pairs = get_region_pairs_with(
            q_img,
            query_regions_ids=q_regions_ids,
            target_regions_ids=t_regions_ids,
        )

        result = get_best_pairs(
            q_img,
            pairs,
            excluded_categories=set(),
            topk=topk,
            user_id=request.user.id,
        )

        return JsonResponse(result, safe=False)

    except (json.JSONDecodeError, ValueError) as e:
        return JsonResponse({"error": f"Invalid data: {e}"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"An error occurred: {e}"}, status=500)


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

        # if there is no similarity retrieved at all, avoid returning the region itself
        if len(list(compared_regions.keys())) == 0:
            return JsonResponse({})
        return JsonResponse(OrderedDict({**current_regions, **compared_regions}))
    except Exception as e:
        log("[get_compared_regions] Couldn't retrieve compared regions", e)
        return JsonResponse(
            {"error": f"Couldn't retrieve compared regions: {e}"}, status=400
        )


def get_similarity_score_range(
    request, wid: int, rid: int | None = None
) -> JsonResponse:
    """
    return a [minScore, maxScore] for all similarities of `wid`
    """
    from django.db.models import Max, Min

    try:
        q = RegionPair.objects.filter(
            (Q(img_1__startswith=f"wit{wid}") & ~Q(score=None))  # pyright: ignore
            | (Q(img_2__startswith=f"wit{wid}") & ~Q(score=None))
        )
        _min = q.aggregate(Min("score"))["score__min"]
        _max = q.aggregate(Max("score"))["score__max"]
        return JsonResponse({"min": _min, "max": _max})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Exception encountered: {e}"}, status=500)


def get_propagated_matches(
    request, wid: int | None = None, rid: int | None = None, img_id: str = ""
) -> JsonResponse:
    """
    formal definition:
    `imgA <exactMatch> imgB`, `imgB <exactMatch> imgC`, `imgC <exactMatch> (imgD, imgE)`
    => `imgA <propagatedMatch> (imgC, imgD, imgE)`

    in other words, given an image `q_img`, a propagated match `p_img` satisfies both conditions:
    - `q_img` not an exact match of `p_img`
    - `p_img` and `q_img` are connected by a chain of intermediate exact matches
        - the number of intermediate exact matches between `q_img` and `p_img` is defined, see `RECURSION_DEPTH`
    - `p_img` and `q_img` may be in the same regions (`RegionPair.regions_id_(1|2)`), but `p_img` and `q_img` cannot have an exact match

    helpful definitions:
    - matches are defined by rows of the `RegionPair` sql table, which describes relations between 2 images `img_1` and `img_2`. relations are undirected (`img1->img2 == img2->img1`)
    - `RegionPair` stores exact matches and other types of matches => an exact match is a special type of match => exact matches are a subset of `RegionPair`
    - an exact match is a relation `(imgA, imgB)` where `RegionPair.category==1`

    process:
    - propagate() : recursively build a list of `(p_img, depth)`
    - propagated_to_regionpair() : filter out results and jsonify results as RegionPairs (tuples of `(query_img, propagated_img)`)

    :returns: JSONified RegionPair tuples
    """
    OG_IMG_ID = img_id
    MAX_DEPTH = 6
    MIN_DEPTH = 1
    RECURSION_DEPTH = [MIN_DEPTH, MAX_DEPTH]

    def get_direct_pairs(q_img: str, _id_regions_array: List[int] = []) -> List[str]:
        img_2_from_1 = RegionPair.objects.values_list("img_2").filter(
            Q(img_1=q_img) & Q(category=1)
        )
        img_1_from_2 = RegionPair.objects.values_list("img_1").filter(
            Q(img_2=q_img) & Q(category=1)
        )
        if len(_id_regions_array):
            img_2_from_1 = img_2_from_1.filter(Q(regions_id_2__in=_id_regions_array))
            img_1_from_2 = img_1_from_2.filter(Q(regions_id_1__in=_id_regions_array))
        return [r[0] for r in list(img_2_from_1.union(img_1_from_2).all())]

    def propagate(
        q_img: str,
        _id_regions_array: List[int] = [],
        _recursion_depth: List[int] = RECURSION_DEPTH,
        depth: int = 0,
        matches: Set[str] = set(),
    ) -> Set[str]:
        """
        :param q_img: query image
        :param _id_regions_array: regions to filter by
        :param _recursion_depth: [min, max] allowed recursion
        :param depth: depth of current step
        :param matches: output results. list of (MatchImage, Depth)
        """
        if depth >= _recursion_depth[1]:
            return matches
        depth += 1
        direct_pairs = get_direct_pairs(q_img, _id_regions_array)
        for new_match in direct_pairs:
            matches.add(new_match)
            matches = propagate(
                new_match,
                _id_regions_array,
                _recursion_depth,
                depth,
                matches,
            )
        return matches

    def propagated_to_regionpair_json(
        _propagated: Set[str], _id_regions_array: List[int] = []
    ) -> List[RegionPairTuple]:
        """
        - remove matches that are
            - exact matches to `OG_IMG_ID`
            - propagations that have already been saved to database
        - format the results
        """
        q_img_regions = regions_from_img(OG_IMG_ID)
        exact_matches_by_regions = get_direct_pairs(OG_IMG_ID, _id_regions_array)
        propagation_2_from_1 = RegionPair.objects.values_list("img_2").filter(
            Q(img_1=OG_IMG_ID) & Q(similarity_type=3)
        )
        propagation_1_from_2 = RegionPair.objects.values_list("img_1").filter(
            Q(img_2=OG_IMG_ID) & Q(similarity_type=3)
        )
        saved_propagations = [
            row[0] for row in propagation_1_from_2.union(propagation_2_from_1)
        ]
        return [
            RegionPair(  # pyright: ignore
                img_1=OG_IMG_ID,
                img_2=p_img,
                regions_id_1=q_img_regions,
                regions_id_2=regions_from_img(p_img),
                category=None,
                category_x=[],
                is_manual=False,
                score=None,
                similarity_type=3,
            ).get_info()
            for p_img in _propagated
            if p_img not in exact_matches_by_regions
            and p_img not in saved_propagations
            and p_img != OG_IMG_ID
        ]

    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)
    try:
        data = json.loads(request.body)
        filter_by_regions: bool = data.get("filterByRegions")
        id_regions_array: List[int] = data.get("regionsIds", [])
        max_recursion_depth = data.get("recursionDepth", MAX_DEPTH)
        recursion_depth = [MIN_DEPTH, max_recursion_depth]
        id_regions_array = (
            id_regions_array
            if filter_by_regions
            and isinstance(id_regions_array, list)
            and len(id_regions_array)
            else []
        )
        propagated = propagate(
            img_id, _id_regions_array=id_regions_array, _recursion_depth=recursion_depth
        )
        return JsonResponse(
            propagated_to_regionpair_json(propagated, id_regions_array), safe=False
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"An error occurred: {e}"}, status=500)


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


def get_regions_title_by_ref(request, wid, rid=None, regions_ref: str | None = None):
    # TODO this is very inefficient: desc generation should not create one DB query per crop, but once per regions_ref
    #   + regions_ref contains the id of the regions which should be extracted
    try:
        regions = Regions.objects.filter(json__ref__startswith=regions_ref).first()
        if regions is None:
            return JsonResponse(
                {"error": f"Regions not found for regions_ref {regions_ref}"},
                status=400,
            )
        return JsonResponse({"title": truncate_char(regions.json["title"], 75)})
    except Exception as e:
        return JsonResponse(
            {"error": f"Error retrieving regions title: {e}"}, status=500
        )


def add_region_pair(request, wid, rid=None):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    def add_jpg(img: str) -> str:
        """
        Ensure the image reference ends with .jpg
        """
        if not img.endswith(".jpg"):
            return f"{img}.jpg"
        return img

    try:
        data = json.loads(request.body)
        q_img, s_img = data.get("q_img"), data.get("s_img")

        if not (validate_img_ref(q_img) and validate_img_ref(s_img)):
            raise ValidationError("Invalid image string format")

        img_1, img_2 = sorted([q_img, s_img], key=sort_key)
        img_1, img_2 = add_jpg(img_1), add_jpg(img_2)

        # todo use rid if defined?
        regions_1, regions_2 = regions_from_img(img_1), regions_from_img(img_2)
        if not regions_1 or not regions_2:
            return JsonResponse({"error": "Unable to find regions"}, status=404)

        try:
            region_pair = RegionPair.objects.get(img_1=img_1, img_2=img_2)
            created = False
            region_pair.similarity_type = 2
            region_pair.is_manual = True

            if region_pair.score == 0 or region_pair.score == 0.0:
                region_pair.score = None

            region_pair = add_user_to_category_x(region_pair, request.user.id)
            region_pair.save()
        except RegionPair.DoesNotExist:
            region_pair = RegionPair.objects.create(
                img_1=img_1,
                img_2=img_2,
                regions_id_1=regions_1,
                regions_id_2=regions_2,
                score=None,
                is_manual=True,
                similarity_type=2,
                category_x=[request.user.id],
            )
            created = True

        s_regions = get_object_or_404(
            Regions, id=regions_2 if q_img == img_1 else regions_1
        )
        return JsonResponse(
            {
                "success": f"Region pair {'created' if created else 'updated'} successfully",
                "s_regions": s_regions.get_json(),
                "pair_info": region_pair.get_info(as_json=True),
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except ValidationError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"An error occurred: {e}"}, status=500)


def no_match(request, wid, rid=None):
    """remove all regionpairs contain q_img image id and the regions id specified in `s_regions`."""
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    try:
        data = json.loads(request.body)
        q_img = data.get("q_img")
        s_regions = data.get(
            "s_regions"
        )  # always a scalar: this function can only be used on a single region
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
    """
    save category on a region pair.
    - if it is a normal similarity (not a propagation), update the category and save.
    - if a propagation does not exist in the database and the user annotates it, add the row to the db and update the category
    - if the propagation exists in the db, is annotated and the user removes the annotation, delete the row from the db
    """
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    try:
        data = json.loads(request.body)

        # img_1 and img_2 are sorted by witness ID.
        # regions_ids are retrieved programmatically instead of from `data` because retrieving from `data` may lead to inconsistencies (regions not aligned with their image), especially in the case of propagated regions.
        img_1, img_2 = sorted([data.get("img_1"), data.get("img_2")], key=sort_key)
        category = data.get("category")
        category = int(data.get("category")) if category else None
        similarity_type = int(data.get("similarity_type", 1))

        query_filter = {
            "img_1": img_1,
            "img_2": img_2,
            # "regions_id_1": regions_id_1,
            # "regions_id_2": regions_id_2,
        }

        to_delete = (
            similarity_type == 3 and category == None
        )  # propagation without category => delete

        if to_delete:
            try:
                region_pair = RegionPair.objects.get(
                    **query_filter,
                )
                region_pair.delete()
                message = f"Deleted 1 propagated region pair"
                pair_info = region_pair.get_info(as_json=True)
            except RegionPair.DoesNotExist:
                message = "Region pair does not exist thus was not deleted"
                pair_info = {}

            return JsonResponse(
                {
                    "status": "success",
                    "message": message,
                    "pair_info": pair_info,
                },
                status=200,
            )

        regions_id_1 = regions_from_img(img_1)
        regions_id_2 = regions_from_img(img_2)

        region_pair, created = RegionPair.objects.update_or_create(
            **query_filter,
            defaults={
                "regions_id_1": regions_id_1,
                "regions_id_2": regions_id_2,
                "category": category,
                "is_manual": data.get("is_manual", False),
                "similarity_type": similarity_type,
            },
        )
        region_pair = add_user_to_category_x(region_pair, request.user.id)
        region_pair.save()

        message = (
            f"New region pair #{region_pair.id} created"
            if created
            else f"Existing region pair #{region_pair.id} updated"
        )

        return JsonResponse(
            {
                "status": "success",
                "message": message,
                "pair_info": region_pair.get_info(as_json=True),
            },
            status=200,
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"An error occurred: {e}"}, status=500)


@user_passes_test(is_superuser)
def index_regions_similarity(request, regions_ref=None):
    """
    Index the content of score files containing regions_ref in their name
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
