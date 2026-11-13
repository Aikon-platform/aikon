from __future__ import annotations

from pathlib import Path

from django.core.management import BaseCommand

from app.similarity.dedupe import BATCH_SIZE
from app.similarity.remap import (
    REMAP_IOU,
    REMAP_IOA,
    build_remap,
    load_plan,
    save_plan,
    apply_remap,
)
from app.webapp.models.digitization import Digitization
from app.webapp.models.document_set import DocumentSet


class Command(BaseCommand):
    help = "Remap the RegionPair images of a document set onto the corrected regions indexed in aiiinotate."

    """
    1. Match
    Each image of a pair belonging to a digitization of the document set is compared to the aiiinotate regions of its canvas:
    - same bbox: unchanged
    - IoU >= `--iou` or IoA >= `--ioa`: renamed (one region) or duplicated (split: one pair per region)
    - no linked region: orphan
    → mapping `{old image: {new image: IoU}}`, can be saved or reloaded with `--plan`

    2. Remap (one locked transaction)
    - renamed images take the anno_id and regions_id of the aiiinotate region
    - a pair with a renamed image of IoU <= 0.8 becomes REMAPPED (score kept, but stale)
    - pairs collapsing onto an existing pair are merged: the existing pair keeps its score and type
    - pairs with an orphan image are deleted (category 1 ones are listed)
    - self-pairs are deleted

    3. Align categories across similarity hashes (as dedupe_regionpairs)

    The command runs as a dry run unless `--apply` is passed
    aiiinotate is never modified
    """

    def add_arguments(self, parser):
        parser.add_argument("document_set_id", type=int)
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Execute changes. Without this, the command is a dry-run.",
        )
        parser.add_argument(
            "--plan",
            type=Path,
            default=None,
            help="JSON path. If it exists, load the mapping from it; otherwise compute and save it here. "
            "A plan is a snapshot: regenerate it if regions or pairs changed since.",
        )
        parser.add_argument(
            "--iou",
            type=float,
            default=REMAP_IOU,
            help=f"IoU threshold (default: {REMAP_IOU})",
        )
        parser.add_argument(
            "--ioa",
            type=float,
            default=REMAP_IOA,
            help=f"IoA threshold (default: {REMAP_IOA})",
        )
        parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)

    def handle(self, *args, **opts):
        log = (
            (lambda s: self.stdout.write(str(s)))
            if opts["verbosity"]
            else (lambda s: None)
        )
        dry_run = not opts["apply"]
        plan_path: Path | None = opts["plan"]
        doc_set = DocumentSet.objects.get(pk=opts["document_set_id"])
        digits = list(Digitization.objects.filter(id__in=doc_set.get_digit_ids()))
        log(f"Document set #{doc_set.id}: {len(digits)} digitizations")

        if plan_path and plan_path.exists():
            mapping, sides, meta = load_plan(plan_path)
            log(
                f"Loaded plan from {plan_path}: {len(mapping)} images (iou={meta.get('iou')}, ioa={meta.get('ioa')})"
            )
        else:
            mapping, sides, stats = build_remap(digits, opts["iou"], opts["ioa"], log)
            if plan_path:
                params = {
                    "document_set": doc_set.id,
                    "iou": opts["iou"],
                    "ioa": opts["ioa"],
                }
                save_plan(mapping, sides, stats, params, plan_path)
                log(f"Saved plan to {plan_path}")

        lost = apply_remap(
            mapping, sides, [d.id for d in digits], opts["batch_size"], log, dry_run
        )
        log(
            f"{len(lost)} pairs of category 1 {'to delete' if dry_run else 'deleted'} (orphan image):"
        )
        for r in lost:
            log(
                f"  #{r['id']} {r['img_1']} | {r['img_2']} (hash={r['similarity_hash']})"
            )
        log("Dry run; re-run with --apply to execute." if dry_run else "Done.")
