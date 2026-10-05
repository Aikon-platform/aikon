from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

from django.db import connection, transaction
from psycopg2.extras import execute_batch

from app.similarity import Bbox, Region
from app.similarity.models.region_pair import parse_img, norm_img, norm_ref, ImgRef
from app.webapp.utils.iiif.annotation import delete_annotation, update_annotation_xywh
from similarity import SimilarityType


"""
Merge duplicate regions in RegionPair.

The same region can be stored under several slightly different coordinates: 
e.g. wit125_man141_0015_550,1395,490,364 and wit125_man141_0015_550,1395,490,370
Overlapping regions of a page are grouped, each group keeps a single name 
and the rows describing the same pair of regions are then merged

Vocabulary:
- canonical name: image name kept for a group of duplicate regions
- mapping: {duplicate image name: canonical name}
- sided fields: fields related to one image of the pair (digit_i, anno_i, regions_id_i)
"""


DEFAULT_THRESHOLD = 0.9
DUPLICATE_IOU = 0.5
PX_TOLERANCE = 0
BATCH_SIZE = 10_000
TYPE_PRIORITY = {2: SimilarityType.MANUAL, 1: SimilarityType.AUTO, 3: SimilarityType.PROPAGATED}
SIDED = ("digit", "anno", "regions_id")
WRITE = [
    "img_1", "img_2", "score", "category", "category_x", "similarity_type",
    *(f"{k}_{i}" for k in SIDED for i in (1, 2)),
]
COLS = ["id", "similarity_hash", *WRITE]

NULL_HASH_DUPLICATES = """
    similarity_hash IS NULL AND (img_1, img_2) IN (
        SELECT img_1, img_2 FROM webapp_regionpair WHERE similarity_hash IS NULL
        GROUP BY 1, 2 HAVING count(*) > 1)
"""
ANNOTATED_CTE = """
    WITH annotated AS (
        SELECT rp.img_1, rp.img_2,
               min(rp.category) AS category,
               count(DISTINCT rp.category) AS n_categories,
               coalesce(array_agg(DISTINCT x ORDER BY x) FILTER (WHERE x IS NOT NULL), '{{}}') AS category_x
        FROM webapp_regionpair rp
        LEFT JOIN LATERAL unnest(rp.category_x) AS x ON true
        WHERE (rp.category IS NOT NULL OR cardinality(rp.category_x) > 0) {scope}
        GROUP BY rp.img_1, rp.img_2
    )
"""
# category_x are compared as sets: their order is not significant
INHERIT_ON = """
    n.img_1 = a.img_1 AND n.img_2 = a.img_2
    AND ((n.category IS NULL AND a.n_categories = 1)
         OR NOT (coalesce(n.category_x, '{}') @> a.category_x AND a.category_x @> coalesce(n.category_x, '{}')))
"""
INHERIT_SET = """
    category = COALESCE(n.category, CASE WHEN a.n_categories = 1 THEN a.category END),
    category_x = a.category_x
"""


def no_log(_: str) -> None:
    pass


# ---------- Geometry ----------
def parse_bbox(s: str) -> Bbox:
    x, y, w, h = (int(float(c)) for c in s.split(","))
    return x, y, w, h


def iou(a: Bbox, b: Bbox) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    iw = max(0, min(ax + aw, bx + bw) - max(ax, bx))
    ih = max(0, min(ay + ah, by + bh) - max(ay, by))
    inter = iw * ih
    union = aw * ah + bw * bh - inter
    return inter / union if union > 0 else 0.0


def canvas(ref: ImgRef) -> tuple[int, int]:
    """page number with digit-specific zero padding"""
    return ref.digit, int(ref.page)


def bbox_iou(a: ImgRef, b: ImgRef) -> float | None:
    """None when the regions are not on the same canvas"""
    return iou(parse_bbox(a.bbox), parse_bbox(b.bbox)) if canvas(a) == canvas(b) else None

def close(a: Bbox, b: Bbox) -> bool:
    return max(abs(x - y) for x, y in zip(a, b)) <= PX_TOLERANCE


def cluster(bboxes: list[Bbox], threshold: float) -> list[list[int]]:
    """
    Produce clusters of overlapping bboxes (all pairs of bboxes IoU >= threshold)
    Most overlapping boxes are merged first, so the result is always the same for a given input
    """
    edges = {
        (i, j): s
        for i, j in combinations(range(len(bboxes)), 2)
        if (s := iou(bboxes[i], bboxes[j])) >= threshold
    }
    owner = list(range(len(bboxes)))
    members = {i: [i] for i in owner}
    for i, j in sorted(edges, key=edges.get, reverse=True):
        a, b = owner[i], owner[j]
        if a != b and all((min(x, y), max(x, y)) in edges for x in members[a] for y in members[b]):
            for x in members[b]:
                owner[x] = a
            members[a] += members.pop(b)
    return list(members.values())


# ---------- Mapping ----------
def fetch_distinct_images(digit_ids: list[int] | None = None) -> set[str]:
    """List of the images in the pairs involving digit_ids (all images if None)"""
    where = "WHERE digit_{i} = ANY(%(d)s)" if digit_ids is not None else ""
    with connection.cursor() as cur:
        cur.execute(
            " UNION ".join(f"SELECT img_{i} FROM webapp_regionpair {where.format(i=i)}" for i in (1, 2)),
            {"d": digit_ids},
        )
        return {r[0] for r in cur}


def build_mapping(threshold: float, log, digit_ids: list[int] | None = None) -> tuple[dict[str, str], dict]:
    """
    Group the overlapping regions of each page → name each group after its largest region
    Returns the mapping of the images to rename and clustering stats
    """
    images = fetch_distinct_images(digit_ids)
    log(f"Loaded {len(images)} distinct images")

    canvases: dict[tuple[int, int], list[Region]] = defaultdict(list)
    skipped = 0
    for img in sorted(images):
        if not (ref := parse_img(img, no_error=True)):
            skipped += 1
        elif ref.bbox:
            canvases[canvas(ref)].append(Region(img, norm_img(ref), parse_bbox(ref.bbox)))
    if skipped:
        log(f"Skipped {skipped} unparseable images")

    mapping: dict[str, str] = {}
    sizes = Counter()
    for regions in canvases.values():
        for cl in cluster([r.box for r in regions], threshold):
            sizes[len(cl)] += 1
            canon = max((regions[i] for i in cl), key=lambda r: r.rank).name
            mapping |= {regions[i].img: canon for i in cl if regions[i].img != canon}

    stats = {
        "distinct_images": len(images),
        "pages_with_regions": len(canvases),
        "cluster_size_histogram": dict(sorted(sizes.items())),
        "images_mapped": len(mapping),
    }
    log(f"Stats: {json.dumps(stats)}")
    return mapping, stats


def save_plan(mapping: dict, stats: dict, threshold: float, path: Path) -> None:
    path.write_text(json.dumps({
        "version": 2,
        "iou_threshold": threshold,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stats": stats,
        "mapping": mapping,
    }, indent=2, sort_keys=True))


def load_plan(path: Path) -> tuple[dict, dict]:
    data = json.loads(path.read_text())
    return data["mapping"], data


# ---------- Rows ----------
def fetch_rows(where: str, params=None) -> list[dict]:
    """
    RegionPair matching SQL WHERE clause
    returns dicts with category_x as a sorted list
    """
    with connection.cursor() as cur:
        cur.execute(f"SELECT {', '.join(COLS)} FROM webapp_regionpair WHERE {where}", params)
        rows = [dict(zip(COLS, r)) for r in cur.fetchall()]
    for r in rows:
        r["category_x"] = sorted(r["category_x"] or [])
    return rows


def fetch_touching(mapping: dict[str, str], where: str = "TRUE") -> list[dict]:
    """RegionPairs containing an image of the mapping (renamed or canonical)"""
    imgs = list({*mapping, *mapping.values()})
    return fetch_rows(f"(img_1 = ANY(%s) OR img_2 = ANY(%s)) AND {where}", [imgs, imgs]) if imgs else []


def swap(r: dict) -> dict:
    return r | {f"{k}_{i}": r[f"{k}_{3 - i}"] for k in ("img", *SIDED) for i in (1, 2)}


def renamed(r: dict, mapping: dict[str, str]) -> dict:
    """Copy of the region_pair with its images renamed, sides swapped if needed to keep img_1 <= img_2"""
    r = r | {f"img_{i}": mapping.get(r[f"img_{i}"], r[f"img_{i}"]) for i in (1, 2)}
    return swap(r) if norm_ref(r["img_2"]) < norm_ref(r["img_1"]) else r


def side_owners(rows, mapping: dict[str, str]) -> dict[str, dict]:
    """
    Sided fields of each canonical image name,
    so that merged pairs inherit the anno_id and regions_id from the canonical image they are merged with
    """
    owners = {}
    for r in sorted(rows, key=lambda r: r["id"]):
        for i in (1, 2):
            img = r[f"img_{i}"]
            if (canon := mapping.get(img, img)) == img or canon == norm_img(img):
                owners.setdefault(canon, {k: r[f"{k}_{i}"] for k in SIDED})
    return owners


def adopt_sides(r: dict, owners: dict[str, dict], targets, mapping: dict[str, str]) -> dict:
    """Copy of the regionPair where each renamed image takes the sided fields of its canonical image name"""
    return r | {
        f"{k}_{i}": v
        for i in (1, 2) if (img := r[f"img_{i}"]) in targets
        for k, v in owners.get(mapping.get(img, img), {}).items()
    }


def merge_group(rows: list[dict]) -> dict:
    """Best pair of a group of duplicates, complemented with the annotations of the others"""
    rows = sorted(rows, key=lambda r: (TYPE_PRIORITY.get(r["similarity_type"], 99), -(r["score"] or 0.0), r["id"]))

    def present(col: str) -> list:
        return [r[col] for r in rows if r[col] not in (None, "")]

    return rows[0] | {
        "score": max(present("score"), default=None),
        "category": min(present("category"), default=None),
        "category_x": sorted({u for r in rows for u in r["category_x"]}),
        "anno_1": next(iter(present("anno_1")), None),
        "anno_2": next(iter(present("anno_2")), None),
    }


# ---------- Execution ----------
def plan_changes(mapping: dict[str, str], null_hash: bool, log, sides: dict[str, dict] | None = None) -> tuple[list[dict], list[int]]:
    """
    Compute (without writing anything) the changes needed to apply the mapping:
    - rows to update: renamed and merged with their duplicates
    - rows to delete: merged duplicates and self-pair regions
    null_hash: also merge manual pairs (no hash) stored several times
    """
    rows = {r["id"]: r for r in [*fetch_touching(mapping), *(fetch_rows(NULL_HASH_DUPLICATES) if null_hash else [])]}
    log(f"Fetched {len(rows)} candidate pairs")
    owners = side_owners(rows.values(), mapping) | (sides or {})
    targets = mapping.keys() | (sides or {}).keys()

    groups = defaultdict(list)
    for r in rows.values():
        r = renamed(adopt_sides(r, owners, targets, mapping), mapping)
        groups[r["img_1"], r["img_2"], r["similarity_hash"]].append(r)

    to_update, to_delete, conflicts = [], [], 0
    for (img_1, img_2, _), group in groups.items():
        if img_1 == img_2:
            to_delete += [r["id"] for r in group]
            continue
        conflicts += len({r["category"] for r in group} - {None}) > 1
        s = merge_group(group)
        if any(s[c] != rows[s["id"]][c] for c in WRITE):
            to_update.append({c: s[c] for c in ("id", *WRITE)})
        to_delete += [r["id"] for r in group if r["id"] != s["id"]]

    log(f"Plan: {len(to_update)} updates, {len(to_delete)} deletions, "
        f"{conflicts} merges with conflicting categories (lowest kept)")
    return to_update, to_delete


def write_changes(to_update: list[dict], to_delete: list[int], batch_size: int) -> None:
    sql = f"UPDATE webapp_regionpair SET {', '.join(f'{c} = %({c})s' for c in WRITE)} WHERE id = %(id)s"
    with connection.cursor() as cur:
        for i in range(0, len(to_delete), batch_size):
            cur.execute("DELETE FROM webapp_regionpair WHERE id = ANY(%s)", [to_delete[i:i + batch_size]])
        execute_batch(cur.cursor, sql, to_update, page_size=batch_size)


def inherit_categories(digit_ids: list[int] | None, dry_run: bool, log) -> None:
    """Apply the category and user ids (category_x) of a pair to all its rows, whatever their hash"""
    scope = "AND (rp.digit_1 = ANY(%(d)s) OR rp.digit_2 = ANY(%(d)s))" if digit_ids else ""
    cte, params = ANNOTATED_CTE.format(scope=scope), {"d": digit_ids}

    with connection.cursor() as cur:
        cur.execute(f"{cte} SELECT count(*) FROM annotated WHERE n_categories > 1", params)
        log(f"{cur.fetchone()[0]} pairs with conflicting categories across hashes (left unchanged)")

        if dry_run:
            cur.execute(f"{cte} SELECT count(*) FROM annotated a JOIN webapp_regionpair n ON {INHERIT_ON}", params)
            log(f"Category inheritance: {cur.fetchone()[0]} rows to update")
        else:
            cur.execute(f"{cte} UPDATE webapp_regionpair n SET {INHERIT_SET} FROM annotated a WHERE {INHERIT_ON}", params)
            log(f"Category inheritance: {cur.rowcount} rows updated")


def apply_mapping(
    mapping: dict[str, str],
    batch_size: int = BATCH_SIZE,
    log=no_log,
    digit_ids: list[int] | None = None,
    dry_run: bool = False,
    sides: dict[str, dict] | None = None
) -> None:
    with transaction.atomic():
        if not dry_run:
            with connection.cursor() as cur:
                cur.execute("LOCK TABLE webapp_regionpair IN SHARE ROW EXCLUSIVE MODE")
        to_update, to_delete = plan_changes(mapping, digit_ids is None, log, sides)

        if not dry_run:
            write_changes(to_update, to_delete, batch_size)

        inherit_categories(digit_ids, dry_run, log)


def dedupe(
    digit_ids: list[int] | None = None,
    threshold: float = DEFAULT_THRESHOLD,
    batch_size: int = BATCH_SIZE,
    log=no_log
) -> None:
    """
    Merge the duplicate regions of the given digitizations (all if None).
    ⚠️ Never call inside a transaction that already wrote to webapp_regionpair (e.g. score_file_to_db):
    that would end up in an infinite wait for each for the other's transaction's lock to end
    """
    mapping, _ = build_mapping(threshold, log, digit_ids)
    apply_mapping(mapping, batch_size, log, digit_ids)


# ---------- Manual merge ----------


def pair_conflicts(mapping: dict[str, str]) -> dict[tuple[str, str], list[int]]:
    """
    After merge of A and B, if A<=>C → cat1 and B<=>C → cat2
    the pairs would carry several categories once renamed, all hashes included
    """
    cats = defaultdict(set)
    for r in (renamed(r, mapping) for r in fetch_touching(mapping, "category IS NOT NULL")):
        if r["img_1"] != r["img_2"]:
            cats[r["img_1"], r["img_2"]].add(r["category"])
    return {p: sorted(c) for p, c in cats.items() if len(c) > 1}


def auto_delete(score: float | None) -> bool:
    """Regions overlapping enough to drop the duplicate annotation without asking"""
    return (score or 0) >= DEFAULT_THRESHOLD


def sync_aiiinotate(keep_anno, drop_anno, keep: ImgRef, score: float | None, delete_drop: bool) -> bool:
    """
    Apply the result of the merge in aiiinotate after merging `drop` into `keep`.
    Returns False if the update failed: the merge must then be rolled back
    """
    if not drop_anno or (keep_anno and keep_anno["@id"] == drop_anno["@id"]):
        return True

    if keep_anno:
        return delete_annotation(drop_anno["@id"]) if delete_drop or auto_delete(score) else True

    # only the dropped region is aiiinotated → overwrite its xywh with the kept region's (same page only)
    return update_annotation_xywh(drop_anno, keep.bbox) if score is not None else True
