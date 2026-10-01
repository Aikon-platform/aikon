from __future__ import annotations

from pathlib import Path

from django.core.management import BaseCommand

from similarity.dedupe import load_plan, build_mapping, save_plan, apply_mapping, DEFAULT_THRESHOLD


class Command(BaseCommand):
    help = (
        "Merge near-duplicate region bboxes (IoU >= threshold) of a same scan page into a single "
        "canonical name in RegionPair, then align categories of rows sharing the same images."
    )

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
        parser.add_argument("--batch-size", type=int, default=10000)

    def handle(self, *args, **opts):
        log = (lambda s: self.stdout.write(str(s))) if opts["verbosity"] else (lambda s: None)
        plan_path: Path | None = opts["plan"]

        if plan_path and plan_path.exists():
            mapping, meta = load_plan(plan_path)
            log(f"Loaded plan from {plan_path}: {len(mapping)} mappings (threshold={meta.get('iou_threshold')})")
        else:
            mapping, stats = build_mapping(opts["threshold"], log, opts["digits"])
            if plan_path:
                save_plan(mapping, stats, opts["threshold"], plan_path)
                log(f"Saved plan to {plan_path}")

        apply_mapping(mapping, opts["batch_size"], log, opts["digits"], dry_run=not opts["apply"])
        log("Done." if opts["apply"] else "Dry run; re-run with --apply to execute.")
