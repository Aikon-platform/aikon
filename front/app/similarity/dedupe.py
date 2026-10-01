from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

from django.db import connection, transaction
from psycopg2.extras import execute_batch

from app.similarity.models.region_pair import parse_img, norm_img, norm_ref, ImgRef
from app.webapp.utils.iiif.annotation import delete_annotation, update_annotation_xywh

Bbox = tuple[int, int, int, int]
DEFAULT_THRESHOLD = 0.9
TYPE_PRIORITY = {2: 0, 1: 1, 3: 2}  # manual > automatic > propagated
SIDED = ("digit", "anno", "regions_id")
WRITE = [
    "img_1", "img_2", "score", "category", "category_x", "similarity_type",
    *(f"{k}_{i}" for k in SIDED for i in (1, 2)),
]
COLS = ["id", "similarity_hash", *WRITE]
DUPLICATE_IOU = 0.5
PX_TOLERANCE = 1

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
INHERIT_ON = """
    n.img_1 = a.img_1 AND n.img_2 = a.img_2
    AND ((n.category IS NULL AND a.n_categories = 1) OR n.category_x IS DISTINCT FROM a.category_x)
"""
INHERIT_SET = """
    category = COALESCE(n.category, CASE WHEN a.n_categories = 1 THEN a.category END),
    category_x = a.category_x
"""


def iou(a: Bbox, b: Bbox) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    iw = max(0, min(ax + aw, bx + bw) - max(ax, bx))
    ih = max(0, min(ay + ah, by + bh) - max(ay, by))
    inter = iw * ih
    union = aw * ah + bw * bh - inter
    return inter / union if union > 0 else 0.0


def cluster(bboxes: list[Bbox], threshold: float) -> list[list[int]]:
    """
    Complete-linkage clustering: a cluster is valid only if all pairwise IoU >= threshold.
    Most overlapping boxes are merged first, so the result is deterministic for a given input order.
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


def parse_bbox(s: str) -> Bbox:
    x, y, w, h = (int(float(c)) for c in s.split(","))
    return x, y, w, h


def fetch_distinct_images(digit_ids: list[int] | None = None) -> set[str]:
    where = "WHERE digit_{} = ANY(%s)" if digit_ids else ""
    with connection.cursor() as cur:
        cur.execute(
            " UNION ".join(f"SELECT img_{i} FROM webapp_regionpair {where.format(i)}" for i in (1, 2)),
            [digit_ids] * 2 if digit_ids else None,
        )
        return {r[0] for r in cur}


def build_mapping(threshold: float, log, digit_ids: list[int] | None = None) -> tuple[dict[str, str], dict]:
    images = fetch_distinct_images(digit_ids)
    log(f"Loaded {len(images)} distinct images")

    groups: dict[tuple, list[tuple[str, str, Bbox]]] = defaultdict(list)
    skipped = 0
    for img in images:
        try:
            ref = parse_img(img)
        except ValueError:
            skipped += 1
            continue
        if ref.bbox is not None:
            groups[ref[:4]].append((img, norm_img(ref), parse_bbox(ref.bbox)))
    if skipped:
        log(f"Skipped {skipped} unparseable images")

    mapping: dict[str, str] = {}
    size_hist: dict[int, int] = defaultdict(int)
    for items in groups.values():
        items.sort()
        bboxes = [b for *_, b in items]
        for cl in cluster(bboxes, threshold):
            size_hist[len(cl)] += 1
            canon = items[max(cl, key=lambda i: (
                bboxes[i][2] * bboxes[i][3], "." not in items[i][0], items[i][0]
            ))][1]
            mapping.update({items[i][0]: canon for i in cl if items[i][0] != canon})

    stats = {
        "distinct_images": len(images),
        "pages_with_regions": len(groups),
        "cluster_size_histogram": dict(sorted(size_hist.items())),
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


def merge_group(rows: list[dict]) -> dict:
    rows = sorted(
        rows,
        key=lambda r: (
            TYPE_PRIORITY.get(r["similarity_type"], 99),
            -(r["score"] or 0.0),
            r["id"],
        ),
    )
    survivor = dict(rows[0])
    x_union: set[int] = set()
    for r in rows:
        if r["category_x"]:
            x_union.update(r["category_x"])
    survivor["category_x"] = sorted(x_union)
    scores = [r["score"] for r in rows if r["score"] is not None]
    survivor["score"] = max(scores) if scores else None
    cats = [r["category"] for r in rows if r["category"] is not None]
    survivor["category"] = min(cats) if cats else None
    survivor["anno_1"] = next((r["anno_1"] for r in rows if r["anno_1"]), None)
    survivor["anno_2"] = next((r["anno_2"] for r in rows if r["anno_2"]), None)
    return survivor


def swap(r: dict) -> dict:
    return {**r, **{f"{k}_{i}": r[f"{k}_{3 - i}"] for k in SIDED for i in (1, 2)}}


def fetch_rows(where: str, params=None) -> list[dict]:
    with connection.cursor() as cur:
        cur.execute(f"SELECT {', '.join(COLS)} FROM webapp_regionpair WHERE {where}", params)
        return [dict(zip(COLS, r)) for r in cur.fetchall()]


def plan_changes(mapping: dict[str, str], null_hash: bool, log, sides: dict[str, dict] | None = None) -> tuple[list[dict], list[int]]:
    imgs = list({*mapping, *mapping.values()})
    rows = fetch_rows("img_1 = ANY(%s) OR img_2 = ANY(%s)", [imgs, imgs]) if imgs else []
    if null_hash:
        rows += fetch_rows(NULL_HASH_DUPLICATES)
    originals = {r["id"]: r for r in rows}
    owners: dict[str, dict] = {}
    for r in sorted(originals.values(), key=lambda r: r["id"]):
        for i in (1, 2):
            img = r[f"img_{i}"]
            canon = mapping.get(img, img)
            if canon == img or norm_img(parse_img(img)) == canon:
                owners.setdefault(canon, {k: r[f"{k}_{i}"] for k in SIDED})
    owners.update(sides or {})
    targets = mapping.keys() | (sides or {}).keys()
    log(f"Fetched {len(originals)} candidate pairs")

    groups = defaultdict(list)
    for r in originals.values():
        r = {**r, **{f"{k}_{i}": v for i in (1, 2)
                     if (img := r[f"img_{i}"]) in targets
                     for k, v in owners.get(mapping.get(img, img), {}).items()}}
        i1, i2 = mapping.get(r["img_1"], r["img_1"]), mapping.get(r["img_2"], r["img_2"])
        if norm_ref(i2) < norm_ref(i1):
            i1, i2, r = i2, i1, swap(r)
        groups[(i1, i2, r["similarity_hash"])].append({**r, "img_1": i1, "img_2": i2})

    to_update, to_delete, conflicts = [], [], 0
    for (i1, i2, _), grp in groups.items():
        if i1 == i2:
            to_delete += [r["id"] for r in grp]
            continue
        conflicts += len({r["category"] for r in grp} - {None}) > 1
        s = merge_group(grp)
        if any(s[c] != originals[s["id"]][c] for c in WRITE):
            to_update.append({c: s[c] for c in ("id", *WRITE)})
        to_delete += [r["id"] for r in grp if r["id"] != s["id"]]

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
    """Apply the category and user matches of a pair to all its rows, whatever their hash"""
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


def apply_mapping(mapping: dict[str, str], batch_size: int, log, digit_ids: list[int] | None = None,
                  dry_run: bool = False, sides: dict[str, dict] | None = None) -> None:
    with transaction.atomic():
        if not dry_run:
            with connection.cursor() as cur:
                cur.execute("LOCK TABLE webapp_regionpair IN SHARE ROW EXCLUSIVE MODE")
        to_update, to_delete = plan_changes(mapping, digit_ids is None, log, sides)
        if not dry_run:
            write_changes(to_update, to_delete, batch_size)
        inherit_categories(digit_ids, dry_run, log)


def dedupe(digit_ids: list[int] | None = None, threshold: float = DEFAULT_THRESHOLD,
           batch_size: int = 10_000, log=lambda s: None) -> None:
    """
    ⚠️ Never call inside a transaction that already wrote to webapp_regionpair (e.g. score_file_to_db):
    upgrading its lock while another import does the same causes a deadlock
    """
    mapping, _ = build_mapping(threshold, log, digit_ids)
    apply_mapping(mapping, batch_size, log, digit_ids)


def pair_conflicts(mapping: dict[str, str]) -> dict[tuple[str, str], list[int]]:
    """Pairs that will carry several categories once renamed, all hashes included"""
    imgs = list({*mapping, *mapping.values()})
    cats = defaultdict(set)
    for r in fetch_rows("(img_1 = ANY(%s) OR img_2 = ANY(%s)) AND category IS NOT NULL", [imgs, imgs]):
        pair = tuple(sorted((mapping.get(r["img_1"], r["img_1"]), mapping.get(r["img_2"], r["img_2"])), key=norm_ref))
        if pair[0] != pair[1]:
            cats[pair].add(r["category"])
    return {p: sorted(c) for p, c in cats.items() if len(c) > 1}


def bbox_iou(a: ImgRef, b: ImgRef) -> float | None:
    """None when the regions are not on the same canvas"""
    same = a[:3] == b[:3] and int(a.page) == int(b.page)
    return iou(parse_bbox(a.bbox), parse_bbox(b.bbox)) if same else None

def close(a: Bbox, b: Bbox) -> bool:
    return max(abs(x - y) for x, y in zip(a, b)) <= PX_TOLERANCE

def sync_aiiinotate(keep_anno, drop_anno, keep: ImgRef, score: float | None, delete_drop: bool) -> bool:
    if keep_anno and drop_anno:
        if keep_anno["@id"] == drop_anno["@id"]:
            return True
        return delete_annotation(drop_anno["@id"]) if delete_drop or (score or 0) >= DEFAULT_THRESHOLD else True
    if drop_anno and score is not None:
        return update_annotation_xywh(drop_anno, keep.bbox)
    return True