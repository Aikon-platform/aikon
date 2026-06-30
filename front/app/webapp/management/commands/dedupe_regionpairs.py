from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import connection, transaction

from app.similarity.models.region_pair import parse_img, norm_ref


Bbox = tuple[int, int, int, int]
TYPE_PRIORITY = {2: 0, 1: 1, 3: 2}  # manual > automatic > propagated


def iou(a: Bbox, b: Bbox) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    iw = max(0, min(ax + aw, bx + bw) - max(ax, bx))
    ih = max(0, min(ay + ah, by + bh) - max(ay, by))
    inter = iw * ih
    union = aw * ah + bw * bh - inter
    return inter / union if union > 0 else 0.0


def cluster(bboxes: list[Bbox], threshold: float) -> list[list[int]]:
    """Complete-linkage clustering: a cluster is valid only if all pairwise IoU >= threshold."""
    n = len(bboxes)
    if n < 2:
        return [[i] for i in range(n)]
    sim = [[1.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            sim[i][j] = sim[j][i] = iou(bboxes[i], bboxes[j])

    clusters = [[i] for i in range(n)]
    while True:
        merged = False
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                if all(
                    sim[a][b] >= threshold for a in clusters[i] for b in clusters[j]
                ):
                    clusters[i] += clusters.pop(j)
                    merged = True
                    break
            if merged:
                break
        if not merged:
            return clusters


def parse_bbox(s: str) -> Bbox:
    x, y, w, h = (int(float(c)) for c in s.split(","))
    return x, y, w, h


def fetch_distinct_images() -> set[str]:
    seen: set[str] = set()
    with connection.cursor() as cur:
        cur.execute("SELECT DISTINCT img_1 FROM webapp_regionpair")
        seen.update(r[0] for r in cur)
        cur.execute("SELECT DISTINCT img_2 FROM webapp_regionpair")
        seen.update(r[0] for r in cur)
    return seen


def build_mapping(threshold: float, log) -> tuple[dict[str, str], dict]:
    images = fetch_distinct_images()
    log(f"Loaded {len(images)} distinct images")

    groups: dict[tuple, list[tuple[str, Bbox]]] = defaultdict(list)
    skipped = 0
    for img in images:
        try:
            ref = parse_img(img)
        except ValueError:
            skipped += 1
            continue
        if ref.bbox is None:
            continue
        groups[(ref.wit, ref.digit_type, ref.digit, ref.page)].append(
            (img, parse_bbox(ref.bbox))
        )
    if skipped:
        log(f"Skipped {skipped} unparseable images")

    mapping: dict[str, str] = {}
    size_hist: dict[int, int] = defaultdict(int)
    for items in groups.values():
        if len(items) < 2:
            continue
        bboxes = [b for _, b in items]
        for cl in cluster(bboxes, threshold):
            size_hist[len(cl)] += 1
            if len(cl) < 2:
                continue
            canon = max(
                cl,
                key=lambda i: (
                    bboxes[i][2] * bboxes[i][3],
                    "." not in items[i][0],
                    items[i][0],
                ),
            )
            for i in cl:
                if i != canon:
                    mapping[items[i][0]] = items[canon][0]

    stats = {
        "distinct_images": len(images),
        "pages_with_regions": sum(1 for v in groups.values() if v),
        "cluster_size_histogram": dict(sorted(size_hist.items())),
        "images_mapped": len(mapping),
    }
    log(f"Stats: {json.dumps(stats)}")
    return mapping, stats


def save_plan(mapping: dict, stats: dict, threshold: float, path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "iou_threshold": threshold,
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "stats": stats,
                "mapping": mapping,
            },
            indent=2,
            sort_keys=True,
        )
    )


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


def apply_mapping(mapping: dict[str, str], batch_size: int, log) -> None:
    if not mapping:
        log("Empty mapping; nothing to apply.")
        return

    cols = [
        "id",
        "img_1",
        "img_2",
        "similarity_hash",
        "score",
        "category",
        "category_x",
        "similarity_type",
        "anno_1",
        "anno_2",
        "digit_1",
        "digit_2",
    ]

    with connection.cursor() as cur:
        cur.execute(
            """
            CREATE TEMP TABLE img_mapping (
                original VARCHAR(150) PRIMARY KEY,
                canonical VARCHAR(150) NOT NULL
            ) ON COMMIT DROP
        """
        )
        cur.executemany(
            "INSERT INTO img_mapping VALUES (%s, %s)", list(mapping.items())
        )
        cur.execute(
            "CREATE TEMP TABLE involved_imgs (img VARCHAR(150) PRIMARY KEY) ON COMMIT DROP"
        )
        cur.execute("INSERT INTO involved_imgs SELECT original FROM img_mapping")
        cur.execute(
            "INSERT INTO involved_imgs SELECT DISTINCT canonical FROM img_mapping ON CONFLICT DO NOTHING"
        )
        cur.execute("ANALYZE involved_imgs")

        cur.execute(
            f"""
            SELECT {', '.join(cols)} FROM webapp_regionpair rp
            WHERE rp.img_1 IN (SELECT img FROM involved_imgs)
               OR rp.img_2 IN (SELECT img FROM involved_imgs)
        """
        )
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    log(f"Fetched {len(rows)} candidate pairs")

    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        ni1 = mapping.get(r["img_1"], r["img_1"])
        ni2 = mapping.get(r["img_2"], r["img_2"])
        if norm_ref(ni2) < norm_ref(ni1):
            ni1, ni2 = ni2, ni1
            r = {
                **r,
                "digit_1": r["digit_2"],
                "digit_2": r["digit_1"],
                "anno_1": r["anno_2"],
                "anno_2": r["anno_1"],
            }
        try:
            r["digit_1"] = parse_img(ni1).digit
            r["digit_2"] = parse_img(ni2).digit
        except ValueError:
            pass
        groups[(ni1, ni2, r["similarity_hash"])].append(r)

    to_update: list[dict] = []
    to_delete: list[int] = []
    for (ni1, ni2, _), grp in groups.items():
        if ni1 == ni2:
            to_delete.extend(r["id"] for r in grp)
            continue
        survivor = merge_group(grp)
        orig = next(r for r in grp if r["id"] == survivor["id"])
        unchanged = (
            len(grp) == 1
            and orig["img_1"] == ni1
            and orig["img_2"] == ni2
            and (orig["category_x"] or []) == survivor["category_x"]
            and orig["score"] == survivor["score"]
            and orig["category"] == survivor["category"]
            and orig["anno_1"] == survivor["anno_1"]
            and orig["anno_2"] == survivor["anno_2"]
            and orig["digit_1"] == survivor["digit_1"]
            and orig["digit_2"] == survivor["digit_2"]
        )
        if not unchanged:
            to_update.append(
                {
                    "id": survivor["id"],
                    "img_1": ni1,
                    "img_2": ni2,
                    "digit_1": survivor["digit_1"],
                    "digit_2": survivor["digit_2"],
                    "anno_1": survivor["anno_1"],
                    "anno_2": survivor["anno_2"],
                    "score": survivor["score"],
                    "category": survivor["category"],
                    "category_x": survivor["category_x"],
                    "similarity_type": survivor["similarity_type"],
                }
            )
        to_delete.extend(r["id"] for r in grp if r["id"] != survivor["id"])

    log(f"Plan: {len(to_update)} updates, {len(to_delete)} deletions")

    update_sql = """
        UPDATE webapp_regionpair SET
            img_1 = %(img_1)s, img_2 = %(img_2)s,
            digit_1 = %(digit_1)s, digit_2 = %(digit_2)s,
            anno_1 = %(anno_1)s, anno_2 = %(anno_2)s,
            score = %(score)s, category = %(category)s,
            category_x = %(category_x)s, similarity_type = %(similarity_type)s
        WHERE id = %(id)s
    """
    with connection.cursor() as cur:
        for i in range(0, len(to_delete), batch_size):
            cur.execute(
                "DELETE FROM webapp_regionpair WHERE id = ANY(%s)",
                [to_delete[i : i + batch_size]],
            )
        for i in range(0, len(to_update), batch_size):
            cur.executemany(update_sql, to_update[i : i + batch_size])


class Command(BaseCommand):
    help = "Detect near-duplicate region bboxes (IoU >= threshold) on the same scan page and merge them into a single canonical name in RegionPair."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Execute changes. Without this, the command is a dry-run.",
        )
        parser.add_argument(
            "--plan",
            type=Path,
            default=None,
            help="JSON path. If it exists, load the mapping from it; otherwise compute and save it here.",
        )
        parser.add_argument(
            "--threshold",
            type=float,
            default=0.95,
            help="IoU threshold for near-duplicate (default: 0.95). Ignored when --plan loads an existing file.",
        )
        parser.add_argument("--batch-size", type=int, default=10000)

    def handle(self, *args, **opts):
        log = (
            (lambda s: self.stdout.write(str(s)))
            if opts["verbosity"]
            else (lambda s: None)
        )
        plan_path: Path | None = opts["plan"]

        if plan_path and plan_path.exists():
            mapping, meta = load_plan(plan_path)
            log(
                f"Loaded plan from {plan_path}: {len(mapping)} mappings (threshold={meta.get('iou_threshold')})"
            )
        else:
            mapping, stats = build_mapping(opts["threshold"], log)
            if plan_path:
                save_plan(mapping, stats, opts["threshold"], plan_path)
                log(f"Saved plan to {plan_path}")

        if not opts["apply"]:
            log("Dry run; re-run with --apply to execute.")
            return

        with transaction.atomic():
            apply_mapping(mapping, batch_size=opts["batch_size"], log=log)
        log("Done.")
