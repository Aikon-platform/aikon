from __future__ import annotations

from pathlib import Path

from django.core.management import BaseCommand

from app.similarity.dedupe import load_plan, build_mapping, save_plan, apply_mapping, purge_orphans, DEFAULT_THRESHOLD, BATCH_SIZE

class Command(BaseCommand):
    help = (
        "Merge near-duplicate region bboxes (IoU >= threshold) of a same scan page into a single "
        "canonical name in RegionPair, then align categories of rows sharing the same images."
    )

    """
    0. Orphans
    Delete pairs whose digitization does not exist or belongs to another witness than in the image name,
    resync digit_1/digit_2 from image names, set regions_id_1/2 of deleted region extractions to NULL
    
    1. Cluster
    On each page, group the regions with IoU ≥ `--threshold` (default 0.9)
    
    2. Name
    Each group takes the canonical name of its smallest region → mapping `{duplicate: canonical}`
    the mapping can be saved or reloaded with `--plan`
    
    3. Merge pairs (one locked transaction)
    - renamed images take the `anno_id` and `regions_id` of the canonical region
    - regionPairs describing the 2 same images with the same hash are merged: 
        → TYPE manual > automatic > propagated
        → SCORE the merged pairs keeps the highest score
        → CATEGORY keep the lowest category and the union of user matches (category_x)
    - self-pairs are deleted (img_1 = img_2)
    
    4. Align categories
    RegionPairs with the same images but different hashes (different similarity computation parameters)
    get the same categories. Conflicting categories are left unchanged
    
    The command runs as a dry run unless `--apply` is passed
    `--digits` restricts it to some digitizations
    aiiinotate is never modified
    """

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
            help="JSON path. If it exists, load the mapping from it; otherwise compute and save it here. "
                 "A plan is a snapshot: regenerate it if pairs changed since.",
        )
        parser.add_argument(
            "--threshold",
            type=float,
            default=DEFAULT_THRESHOLD,
            help=f"IoU threshold for near-duplicate (default: {DEFAULT_THRESHOLD}). Ignored when --plan loads an existing file.",
        )
        parser.add_argument(
            "--digits",
            type=lambda s: [int(d) for d in s.split(",")],
            default=None,
            help="Comma-separated digitization ids to restrict the dedupe to (skips the NULL-hash pass).",
        )
        parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)

    def handle(self, *args, **opts):
        log = (lambda s: self.stdout.write(str(s))) if opts["verbosity"] else (lambda s: None)
        dry_run = not opts["apply"]
        plan_path: Path | None = opts["plan"]

        purge_orphans(dry_run, log)
        if plan_path and plan_path.exists():
            mapping, meta = load_plan(plan_path)
            log(f"Loaded plan from {plan_path}: {len(mapping)} mappings (threshold={meta.get('iou_threshold')})")
        else:
            mapping, stats = build_mapping(opts["threshold"], log, opts["digits"])
            if plan_path:
                save_plan(mapping, stats, opts["threshold"], plan_path)
                log(f"Saved plan to {plan_path}")

        apply_mapping(mapping, opts["batch_size"], log, opts["digits"], dry_run=dry_run)
        log("Dry run; re-run with --apply to execute." if dry_run else "Done.")
