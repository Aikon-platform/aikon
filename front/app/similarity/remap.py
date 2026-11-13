from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from itertools import count, product
from pathlib import Path

from django.db import connection, transaction
from psycopg2.extras import execute_batch

from app.similarity import Bbox, SimilarityType
from app.similarity.dedupe import (
    BATCH_SIZE,
    WRITE,
    close,
    db_oriented,
    fetch_distinct_images,
    fetch_rows,
    inherit_categories,
    merge_group,
    no_log,
    oriented,
    parse_bbox,
    write_changes,
)
from app.similarity.models.region_pair import norm_img, parse_img
from app.webapp.models.digitization import Digitization
from app.webapp.utils.iiif.annotation import (
    get_coord_from_annotation,
    get_id_from_annotation,
    get_manifest_annotations,
    get_regions_id_from_annotation,
)

"""
Remap the images of RegionPair onto the corrected regions indexed in aiiinotate.

Each image of a pair (old bbox) is matched with the aiiinotate regions of its canvas:
- unchanged: a region has the same bbox → left as is
- linked: regions with IoU >= iou or IoA >= ioa → renamed (one region) or duplicated (split, one pair per region)
- orphan: no linked region → its pairs are deleted
A renamed image with IoU <= EQUIV_IOU makes its pair REMAPPED (score kept but stale)
Pairs collapsing onto an existing pair are merged: the existing pair keeps its score and type

Vocabulary:
- mapping: {old image: {new image: IoU}}, {} for an orphan
- sides: {new image: sided fields (digit, anno, regions_id) from aiiinotate}
"""

REMAP_IOU = 0.5
REMAP_IOA = 0.8
EQUIV_IOU = 0.8


# ---------- Geometry ----------
def overlaps(a: Bbox, b: Bbox) -> tuple[float, float]:
    """(IoU, intersection over the smallest area)"""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    inter = max(0, min(ax + aw, bx + bw) - max(ax, bx)) * max(
        0, min(ay + ah, by + bh) - max(ay, by)
    )
    return inter / ((aw * ah + bw * bh - inter) or 1), inter / (
        min(aw * ah, bw * bh) or 1
    )


# ---------- Mapping ----------
def canvas_regions(digit: Digitization) -> dict[int, list[tuple[Bbox, dict]]]:
    """{canvas number: [(bbox, sided fields)]} of the regions indexed in aiiinotate"""
    regions = defaultdict(list)
    for a in get_manifest_annotations(digit.get_ref(), only_ids=False):
        page = int(a["on"][0]["full"].split("/canvas/c")[1].split(".json")[0])
        regions[page].append(
            (
                parse_bbox(get_coord_from_annotation(a, as_str=True)),
                {
                    "digit": digit.id,
                    "anno": get_id_from_annotation(a),
                    "regions_id": get_regions_id_from_annotation(a),
                },
            )
        )
    return regions


def build_remap(
    digits: list[Digitization],
    iou_min: float = REMAP_IOU,
    ioa_min: float = REMAP_IOA,
    log=no_log,
) -> tuple[dict[str, dict[str, float]], dict[str, dict], dict]:
    regions = {}
    for d in digits:
        if r := canvas_regions(d):
            regions[d.id] = r
        else:
            log(
                f"Digitization #{d.id}: no region in aiiinotate (or request failed), skipped"
            )

    images = fetch_distinct_images(list(regions))
    mapping, sides, stats = {}, {}, Counter()
    for img in sorted(images):
        ref = parse_img(img, no_error=True)
        if not (ref and ref.bbox):
            stats["skipped"] += 1
            continue
        box = parse_bbox(ref.bbox)
        page = regions[ref.digit].get(int(ref.page), [])
        if any(close(box, b) for b, _ in page):
            stats["unchanged"] += 1
            continue
        linked = {}
        for b, side in page:
            s_iou, s_ioa = overlaps(box, b)
            if s_iou >= iou_min or s_ioa >= ioa_min:
                name = norm_img(ref._replace(bbox=",".join(map(str, b))))
                linked[name], sides[name] = s_iou, side
        mapping[img] = linked
        stats[
            "orphan"
            if not linked
            else "split"
            if len(linked) > 1
            else "equivalent"
            if max(linked.values()) > EQUIV_IOU
            else "remapped"
        ] += 1

    stats = {"distinct_images": len(images), **dict(sorted(stats.items()))}
    log(f"Stats: {json.dumps(stats)}")
    return mapping, sides, stats


def save_plan(mapping, sides, stats, params: dict, path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "version": 1,
                **params,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "stats": stats,
                "mapping": mapping,
                "sides": sides,
            },
            indent=2,
            sort_keys=True,
        )
    )


def load_plan(path: Path) -> tuple[dict, dict, dict]:
    data = json.loads(path.read_text())
    return data["mapping"], data["sides"], data


# ---------- Rows ----------
def expand(r: dict, mapping: dict, sides: dict):
    """Copies of the pair, one per combination of new images"""
    for (a, iou_a), (b, iou_b) in product(
        *(mapping.get(r[f"img_{i}"], {r[f"img_{i}"]: 1.0}).items() for i in (1, 2))
    ):
        moved = {
            f"{k}_{i}": v
            for i, old, new in ((1, r["img_1"], a), (2, r["img_2"], b))
            if old in mapping
            for k, v in sides[new].items()
        }
        stale = (
            {"similarity_type": SimilarityType.REMAPPED}
            if min(iou_a, iou_b) <= EQUIV_IOU
            else {}
        )
        yield oriented(r | {"img_1": a, "img_2": b} | moved | stale)


def plan_changes(
    mapping: dict, sides: dict, log
) -> tuple[list[dict], list[dict], list[int], list[dict]]:
    """(rows to update, rows to insert, ids to delete, deleted pairs of category 1 with an orphan image)"""
    imgs = list({*mapping, *sides})
    rows = (
        {
            r["id"]: r
            for r in fetch_rows("img_1 = ANY(%s) OR img_2 = ANY(%s)", [imgs, imgs])
        }
        if imgs
        else {}
    )
    log(f"Fetched {len(rows)} candidate pairs")

    orphans = {img for img, linked in mapping.items() if not linked}
    to_delete = [i for i, r in rows.items() if {r["img_1"], r["img_2"]} & orphans]
    lost = [rows[i] for i in to_delete if rows[i]["category"] == 1]

    new_id, groups = count(-1, -1), defaultdict(list)
    for i in rows.keys() - set(to_delete):
        for n, r in enumerate(expand(rows[i], mapping, sides)):
            r = r | {"id": next(new_id)} if n else r
            groups[r["img_1"], r["img_2"], r["similarity_hash"]].append(r)

    to_update, to_insert = [], []
    for (img_1, img_2, _), group in groups.items():
        if img_1 == img_2:
            to_delete += [r["id"] for r in group if r["id"] > 0]
            continue
        s = merge_group(group)
        if fresh := [
            r for r in group if r["similarity_type"] != SimilarityType.REMAPPED
        ]:
            s["score"] = merge_group(fresh)["score"]
        if s["id"] < 0:
            to_insert.append(s)
        elif any(s[c] != rows[s["id"]][c] for c in WRITE):
            to_update.append(s)
        to_delete += [r["id"] for r in group if 0 < r["id"] != s["id"]]

    log(
        f"Plan: {len(to_update)} updates, {len(to_insert)} insertions (splits), {len(to_delete)} deletions"
    )
    return to_update, to_insert, to_delete, lost


def insert_rows(rows: list[dict], batch_size: int) -> None:
    cols = ["similarity_hash", *WRITE]
    sql = f"INSERT INTO webapp_regionpair ({', '.join(cols)}) VALUES ({', '.join(f'%({c})s' for c in cols)})"
    with connection.cursor() as cur:
        execute_batch(cur.cursor, sql, db_oriented(rows), page_size=batch_size)


def apply_remap(
    mapping: dict,
    sides: dict,
    digit_ids: list[int],
    batch_size: int = BATCH_SIZE,
    log=no_log,
    dry_run: bool = False,
) -> list[dict]:
    """Returns the deleted pairs of category 1 that had an orphan image"""
    with transaction.atomic():
        if not dry_run:
            with connection.cursor() as cur:
                cur.execute("LOCK TABLE webapp_regionpair IN SHARE ROW EXCLUSIVE MODE")
        to_update, to_insert, to_delete, lost = plan_changes(mapping, sides, log)

        if not dry_run:
            write_changes(to_update, to_delete, batch_size)
            insert_rows(to_insert, batch_size)

        inherit_categories(digit_ids, dry_run, log)
    return lost
