import json
import re
from collections import OrderedDict
from typing import List

from django.db.models import Q, Count
from django.shortcuts import get_object_or_404
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.db import transaction, connection

from django.contrib.auth.decorators import user_passes_test

from app.similarity.models.region_pair import RegionPair, parse_img, add_jpg
from app.webapp.models.regions import Regions
from app.webapp.models.witness import Witness
from app.webapp.utils.functions import (
    truncate_char,
    safe_float,
    safe_int,
    parse_list,
    safe_bool,
)
from app.webapp.utils.logger import log
from app.similarity.utils import (
    send_request,
    check_computed_pairs,
    get_computed_pairs,
    get_best_pairs,
    get_region_pairs_with,
    get_digit_imgs,
    validate_img_ref,
    get_matched_regions,
    get_all_pairs,
    reset_similarity,
    update_category_x,
    filter_pairs,
    retrieve_pair,
    SimilarityType,
    build_pairs_query,
    stream_pairs_ndjson,
    normalize_pair,
)
from app.webapp.utils.tasking import receive_notification
from app.webapp.views import is_superuser, check_ref
from app.webapp.models.digitization import Digitization
from app.webapp.models.document_set import DocumentSet


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

    q_digit_ids = {q_r.digitization_id for q_r in q_regions}

    if not len(q_regions):
        return JsonResponse(
            {"error": f"No regions found for this witness #{wid}"}, status=400
        )

    try:
        data = json.loads(request.body.decode("utf-8"))
        filter_by_regions = data.get("filterByRegions", True)

        t_digit_ids = data.get("digitIds", [])
        if not t_digit_ids and data.get("regionsIds", []):
            t_digit_ids = list(
                Regions.objects.filter(id__in=data.get("regionsIds", []))
                .values_list("digitization_id", flat=True)
                .distinct()
            )

        q_img = str(data.get("qImg", ""))
        topk = min(max(int(data.get("topk") or 10), 1), 20)

        if not q_img:
            return JsonResponse({})

        if filter_by_regions and not t_digit_ids:
            return JsonResponse({})

        pairs = get_region_pairs_with(
            q_img,
            query_digit_ids=q_digit_ids,
            target_digit_ids=t_digit_ids if filter_by_regions else None,
        )

        result = get_best_pairs(
            q_img,
            pairs,
            excluded_categories=set(),
            topk=topk,
            user_id=request.user.id,
        )

        # Set to false to display pairs containing the same image multiple times with different scores
        no_duplicates = True
        if no_duplicates:
            seen = set()
            s_img_idx = 2
            result = [
                p
                for p in result
                if not (p[s_img_idx] in seen or seen.add(p[s_img_idx]))
            ]

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
        q_digit_ids = {q_r.digitization_id for q_r in q_regions}

        pairs = RegionPair.objects.filter(
            Q(digit_1__in=q_digit_ids) | Q(digit_2__in=q_digit_ids)
        ).values_list("digit_1", "digit_2")

        partner_ids = set()
        for d1, d2 in pairs:
            if d1 in q_digit_ids:
                partner_ids.add(d2)
            if d2 in q_digit_ids:
                partner_ids.add(d1)
        partner_ids -= q_digit_ids

        partner_regions = Regions.objects.filter(digitization_id__in=partner_ids)

        compared_regions = dict(
            sorted(
                {r.get_ref(): r.get_json() for r in partner_regions}.items(),
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
        digit_ids = list(
            Digitization.objects.filter(witness_id=wid).values_list("id", flat=True)
        )
        q = RegionPair.objects.filter(
            (Q(digit_1__in=digit_ids) & ~Q(score=None))
            | (Q(digit_2__in=digit_ids) & ~Q(score=None))
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
    Given an image `img_id`, find all images reachable through a chain of exact matches
    (category=1), excluding direct exact matches and already-saved propagations.

    Uses a recursive SQL CTE instead of Python-level recursion for O(1) queries
    regardless of graph size and depth.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    try:
        data = json.loads(request.body)
        filter_by_digit: bool = data.get("filterByRegions", False)
        digit_ids: List[int] = data.get("digitIds", data.get("regionsIds", []))
        max_depth = min(int(data.get("recursionDepth", 6)), 6)

        if not (filter_by_digit and isinstance(digit_ids, list) and digit_ids):
            digit_ids = []

        propagated_imgs = _propagate_cte(img_id, max_depth, digit_ids or None)

        if not propagated_imgs:
            return JsonResponse([], safe=False)

        q_ref = parse_img(add_jpg(img_id))
        result = []
        for p_img in propagated_imgs:
            try:
                p_ref = parse_img(p_img)
                result.append(
                    [None, img_id, p_img, q_ref.digit, p_ref.digit, None, [], 3, None]
                )
            except ValueError:
                continue

        return JsonResponse(result, safe=False)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"An error occurred: {e}"}, status=500)


def _propagate_cte(
    q_img: str, max_depth: int, digit_ids: List[int] | None = None
) -> List[str]:
    table = RegionPair._meta.db_table
    has_filter = bool(digit_ids)

    fwd_filter = "AND digit_2 = ANY(%(dids)s)" if has_filter else ""
    rev_filter = "AND digit_1 = ANY(%(dids)s)" if has_filter else ""
    rec_filter = (
        "AND (CASE WHEN rp.img_1 = c.img THEN rp.digit_2"
        " ELSE rp.digit_1 END = ANY(%(dids)s))"
        if has_filter
        else ""
    )

    sql = f"""
    WITH RECURSIVE chain(img, depth) AS (
        SELECT img_2, 1 FROM {table}
        WHERE img_1 = %(q)s AND category = 1 {fwd_filter}
        UNION
        SELECT img_1, 1 FROM {table}
        WHERE img_2 = %(q)s AND category = 1 {rev_filter}
        UNION
        SELECT
            CASE WHEN rp.img_1 = c.img THEN rp.img_2 ELSE rp.img_1 END,
            c.depth + 1
        FROM {table} rp
        INNER JOIN chain c ON (rp.img_1 = c.img OR rp.img_2 = c.img)
        WHERE rp.category = 1 AND c.depth < %(max_depth)s {rec_filter}
    )
    SELECT DISTINCT img FROM chain
    WHERE img != %(q)s
      AND img NOT IN (
          SELECT img_2 FROM {table} WHERE img_1 = %(q)s AND category = 1 {fwd_filter}
          UNION
          SELECT img_1 FROM {table} WHERE img_2 = %(q)s AND category = 1 {rev_filter}
      )
      AND img NOT IN (
          SELECT img_2 FROM {table} WHERE img_1 = %(q)s AND similarity_type = 3
          UNION
          SELECT img_1 FROM {table} WHERE img_2 = %(q)s AND similarity_type = 3
      )
    """

    params = {"q": q_img, "max_depth": max_depth}
    if has_filter:
        params["dids"] = list(digit_ids)

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        return [row[0] for row in cursor.fetchall()]


def get_regions_title_by_ref(request, wid, rid=None, regions_ref: str | None = None):
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

    try:
        data = json.loads(request.body)
        q_img, s_img = data.get("q_img"), data.get("s_img")

        if not (validate_img_ref(q_img) and validate_img_ref(s_img)):
            raise ValidationError("Invalid image string format")

        img_1, img_2 = RegionPair.order_pair((q_img, s_img))
        img_1, img_2 = add_jpg(img_1), add_jpg(img_2)
        ref1, ref2 = parse_img(img_1), parse_img(img_2)

        try:
            region_pair = RegionPair.objects.get(img_1=img_1, img_2=img_2)
            created = False
            region_pair.similarity_type = SimilarityType.MANUAL

            if region_pair.score == 0 or region_pair.score == 0.0:
                region_pair.score = None

            region_pair = update_category_x(region_pair, request.user.id)
            region_pair.save(validate=True)
        except RegionPair.DoesNotExist:
            region_pair = RegionPair.objects.create(
                img_1=img_1,
                img_2=img_2,
                digit_1=ref1.digit,
                digit_2=ref2.digit,
                score=None,
                similarity_type=SimilarityType.MANUAL,
                category_x=[request.user.id],
            )
            created = True

        return JsonResponse(
            {
                "success": f"Region pair {'created' if created else 'updated'} successfully",
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
        s_digit_id = data.get("s_digit_id", data.get("s_regions"))
        pairs = get_matched_regions(q_img, s_digit_id)
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
            q_imgs.update(get_digit_imgs(q_r.digitization_id))
        return JsonResponse(sorted(list(q_imgs)), safe=False)
    except Exception as e:
        return JsonResponse(
            {
                "error": f"Couldn't retrieve images of regions #{rid} in the database: {e}"
            },
            status=400,
        )


def add_user_to_pair(request):
    """
    Toggle the current user in the category_x list of all region pairs
    matching img_1 and img_2. Creates the pair if none exist.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    try:
        data = json.loads(request.body)
        img_1, img_2 = RegionPair.order_pair((data.get("img_1"), data.get("img_2")))
        user_id = request.user.id

        query = {"img_1": img_1, "img_2": img_2}
        rp_list = list(RegionPair.objects.filter(**query))

        if rp_list:
            for rp in rp_list:
                category_x = rp.category_x or []
                if user_id in category_x:
                    category_x.remove(user_id)
                else:
                    category_x.append(user_id)
                rp.category_x = category_x
                rp.save()
            message = f"Updated {len(rp_list)} region pair(s)"
        else:
            ref1, ref2 = parse_img(img_1), parse_img(img_2)
            rp = RegionPair.objects.create(
                **query,
                category_x=[user_id],
                digit_1=ref1.digit,
                digit_2=ref2.digit,
            )
            message = f"New region pair #{rp.id} created"

        return JsonResponse({"status": "success", "message": message}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        log("[add_user_to_pair] An error occurred", e)
        return JsonResponse({"error": f"An error occurred: {e}"}, status=500)


def save_category(request):
    """
    Save category on all region pairs matching img_1 and img_2.
    - Creates pair if none exist
    - For propagated pairs: deletes all matching rows if category is removed
    """
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    try:
        data = json.loads(request.body)
        img_1, img_2 = RegionPair.order_pair((data.get("img_1"), data.get("img_2")))
        category = data.get("category")
        category = int(category) if category else None
        similarity_type = int(data.get("similarity_type") or SimilarityType.MANUAL)

        query = {"img_1": img_1, "img_2": img_2}

        # propagation without category => delete all
        if similarity_type == SimilarityType.PROPAGATED and category is None:
            deleted, _ = RegionPair.objects.filter(**query).delete()
            return JsonResponse(
                {
                    "status": "success",
                    "message": f"Deleted {deleted} propagated region pair(s)",
                },
                status=200,
            )

        rp_list = list(RegionPair.objects.filter(**query))

        if rp_list:
            for rp in rp_list:
                rp.category = category
                rp.save()
            message = f"Updated {len(rp_list)} region pair(s)"
        else:
            RegionPair.objects.create(
                **query,
                category=category,
                similarity_type=similarity_type,
                category_x=[],
                digit_1=parse_img(img_1).digit,
                digit_2=parse_img(img_2).digit,
            )
            message = "New region pair created"

        return JsonResponse({"status": "success", "message": message}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        log("[save_category] An error occurred", e)
        return JsonResponse({"error": f"An error occurred: {e}"}, status=500)


def exact_match(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    try:
        data = json.loads(request.body)
        img_1, img_2 = RegionPair.order_pair((data.get("img_1"), data.get("img_2")))

        region_pair, msg = retrieve_pair(img_1, img_2, create=True)
        if not region_pair:
            return JsonResponse(
                {"error": msg},
                status=400,
            )

        if region_pair.category == 1:
            return JsonResponse(
                {
                    "status": "success",
                    "message": "Pair is already tagged as exact match",
                    "pair_info": region_pair.get_info(as_json=True),
                },
                status=200,
            )
        region_pair.category = 1  # exact match
        region_pair.save()

        return JsonResponse(
            {
                "status": "success",
                "message": "Pair successfully tagged as exact match",
                "pair_info": region_pair.get_info(as_json=True),
            },
            status=200,
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"An error occurred: {e}"}, status=500)


@transaction.atomic
def exact_match_batch(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    try:
        data = json.loads(request.body)
        results = {"created": 0, "updated": 0}

        pairs = [normalize_pair(p["img_1"], p["img_2"]) for p in data.get("pairs", [])]

        if not pairs:
            return JsonResponse({"status": "success", "results": results})

        unique_img_pairs = {(img_1, img_2) for img_1, img_2 in pairs}

        q = Q()
        for img_1, img_2 in unique_img_pairs:
            q |= Q(img_1=img_1, img_2=img_2)

        existing = set(
            RegionPair.objects.filter(q).values_list("img_1", "img_2").distinct()
        )

        # Create missing
        to_create = []
        created_keys = set()
        for img_1, img_2 in pairs:
            key = (img_1, img_2)
            if key not in existing and key not in created_keys:
                created_keys.add(key)
                ref1, ref2 = parse_img(img_1), parse_img(img_2)
                to_create.append(
                    RegionPair(
                        img_1=img_1,
                        img_2=img_2,
                        digit_1=ref1.digit,
                        digit_2=ref2.digit,
                        category=1,
                        similarity_type=SimilarityType.PROPAGATED,
                        score=None,
                        category_x=[],
                    )
                )

        if to_create:
            RegionPair.objects.bulk_create(to_create)
            results["created"] = len(to_create)

        if existing:
            results["updated"] = (
                RegionPair.objects.filter(q).exclude(category=1).update(category=1)
            )

        return JsonResponse({"status": "success", "results": results})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        log("[exact_match_batch] Exception encountered", e)
        return JsonResponse({"error": str(e)}, status=500)


@transaction.atomic
def uncategorize_pair_batch(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    try:
        data = json.loads(request.body)

        pairs = set()
        for p in data.get("pairs", []):
            pairs.add(normalize_pair(p.get("img_1"), p.get("img_2")))

        if not pairs:
            return JsonResponse({"status": "success", "uncategorized": 0})

        q = Q()
        for img_1, img_2 in pairs:
            q |= Q(img_1=img_1, img_2=img_2)

        uncategorized = (
            RegionPair.objects.filter(q)
            .exclude(category__isnull=True)
            .update(category=None)
        )

        return JsonResponse({"status": "success", "uncategorized": uncategorized})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


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


# @user_passes_test(is_superuser)
# def remove_incorrect_pairs(request, mismatched=False, duplicate=False, swapped=True):
#     """
#     Removes RegionPair instances that are faulty
#     """
#     from django.db import DatabaseError
#
#     count = 0
#
#     try:
#         if mismatched:
#             from django.db.models import F
#
#             # if img_1 is alphabetically after img_2,
#             # indicating that the pair has been incorrectly inserted in the database
#             mismatched_pairs = RegionPair.objects.filter(img_1__gt=F("img_2"))
#             count += mismatched_pairs.count()
#             mismatched_pairs.delete()
#
#         if duplicate:
#             # if there is duplicates of the same img pair with different ids
#             duplicate_pairs = (
#                 RegionPair.objects.values("img_1", "img_2")
#                 .annotate(count=Count("id"))
#                 .filter(count__gt=1)
#             )
#             count += len(duplicate_pairs)
#             for pair in duplicate_pairs:
#                 duplicates = RegionPair.objects.filter(
#                     img_1=pair["img_1"], img_2=pair["img_2"]
#                 )
#                 count += duplicates.count() - 1
#                 duplicates[1:].delete()
#
#         if swapped:
#             # if there is duplicates of the same img pair but with img_1 and img_2 swapped
#             swapped_pairs = RegionPair.objects.filter(
#                 Q(img_1__in=RegionPair.objects.values("img_2"))
#                 & Q(img_2__in=RegionPair.objects.values("img_1"))
#             )
#             count += len(swapped_pairs)
#             for pair in swapped_pairs:
#                 reverse_pair = RegionPair.objects.filter(
#                     img_1=pair.img_2, img_2=pair.img_1
#                 ).first()
#                 if reverse_pair:
#                     sorted_imgs = RegionPair.order_pair((pair.img_1, pair.img_2))
#                     if pair.img_1 != sorted_imgs[0]:
#                         pair.delete()
#                     else:
#                         reverse_pair.delete()
#
#         return JsonResponse({"message": f"{count} incorrect pairs removed"})
#
#     except DatabaseError as e:
#         return JsonResponse(
#             {"message": f"An error occurred while removing incorrect pairs: {e}"},
#             status=500,
#         )


# MARKER MARKER do not use rid
def get_regions_pairs(request, wid, rid=None):
    """
    Return all the region pairs for a given region id or witness id.
    Filters on digit_ids derived from witness/regions.

    URL arguments:
    - minScore, maxScore, topk, category, excludeSelf
    - regionsIds: comma-separated digitization IDs (legacy name kept for API compat)
    - witnessIds: comma-separated witness IDs
    """
    if rid is not None:
        regions = [get_object_or_404(Regions, id=rid)]
    else:
        witness = get_object_or_404(Witness, id=wid)
        regions = witness.get_regions()

    if not len(regions):
        return JsonResponse(
            {"error": f"No regions found for this witness #{wid}"}, status=400
        )

    digit_ids_param = request.GET.get("regionsIds", "")
    witness_ids_param = request.GET.get("witnessIds", "")

    digit_ids = set()
    if digit_ids_param:
        try:
            digit_ids.update(int(d) for d in digit_ids_param.split(","))
        except ValueError:
            return JsonResponse({"error": "Invalid regionsIds parameter"}, status=400)

    if witness_ids_param:
        try:
            for w in witness_ids_param.split(","):
                digit_ids.update(
                    Digitization.objects.filter(witness_id=int(w)).values_list(
                        "id", flat=True
                    )
                )
        except ValueError:
            return JsonResponse({"error": "Invalid witnessIds parameter"}, status=400)

    # Always include the current witness's digit_ids
    digit_ids.update(r.digitization_id for r in regions)

    try:
        pairs = filter_pairs(
            digit_ids,
            exclusive=bool(witness_ids_param or digit_ids_param),
            min_score=safe_float(request.GET.get("minScore")),
            max_score=safe_float(request.GET.get("maxScore")),
            topk=safe_int(request.GET.get("topk")),
            exclude_self=safe_bool(request.GET.get("excludeSelf")) or False,
            categories=parse_list(request.GET.get("category")) or [],
        )
        return JsonResponse(pairs, status=200, safe=False)
    except Exception as e:
        return JsonResponse({"error": f"An error occurred: {e}"}, status=500)


def get_document_set_pairs(request, dsid=None):
    if dsid is None:
        return JsonResponse({"error": "No document set id provided"}, status=400)

    document_set = DocumentSet.objects.get(id=dsid)
    if document_set is None:
        return JsonResponse(
            {"error": f"Document set #{dsid} does not exist"}, status=400
        )

    digit_ids = document_set.digit_ids
    if not digit_ids:
        return JsonResponse(
            {"error": f"No digitizations found for this document set #{dsid}"},
            status=400,
        )

    try:
        pairs = filter_pairs(
            digit_ids,
            exclusive=True,
            min_score=safe_float(request.GET.get("minScore")),
            max_score=safe_float(request.GET.get("maxScore")),
            topk=safe_int(request.GET.get("topk")),
            exclude_self=safe_bool(request.GET.get("excludeSelf")) or False,
            categories=parse_list(request.GET.get("category")),
        )
        return JsonResponse(pairs, status=200, safe=False)
    except Exception as e:
        return JsonResponse({"error": f"An error occurred: {e}"}, status=500)


def stream_document_set_pairs(request, dsid=None):
    """
    Streams pairs as NDJSON

    Query params:
        category: comma-separated category IDs (0 = uncategorized)
        minScore, maxScore: score range filter
        topk: limit results
        excludeSelf: exclude same-document pairs
        compress: if 'true', return gzip-compressed response
    """
    if dsid is None:
        return JsonResponse({"error": "No document set id provided"}, status=400)

    try:
        document_set = DocumentSet.objects.get(id=dsid)
    except Exception:
        return JsonResponse(
            {"error": f"Document set #{dsid} does not exist"}, status=400
        )

    digit_ids = document_set.digit_ids
    if not digit_ids:
        return JsonResponse(
            {"error": f"No digitizations found for document set #{dsid}"}, status=400
        )

    params = {
        "categories": parse_list(request.GET.get("category")),
        "min_score": safe_float(request.GET.get("minScore")),
        "max_score": safe_float(request.GET.get("maxScore")),
        "topk": safe_int(request.GET.get("topk")),
        "exclude_self": safe_bool(request.GET.get("excludeSelf")) or False,
    }

    sql, sql_params = build_pairs_query(digit_ids, **params)

    response = StreamingHttpResponse(
        stream_pairs_ndjson(sql, sql_params), content_type="application/x-ndjson"
    )

    # Nginx streaming headers
    response["X-Accel-Buffering"] = "no"
    response["Cache-Control"] = "no-cache, no-store"
    response["X-Content-Type-Options"] = "nosniff"

    return response
