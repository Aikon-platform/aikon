import re
import json
from datetime import datetime
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import connection, transaction

from app.similarity.models.region_pair import RegionPair
from app.webapp.models.regions import Regions


IMG_RE = re.compile(r"^wit(\d+)_(\w{3})(\d+)_(\d+)(?:_([\d,]+))?\.jpg$")


def parse_img(img: str) -> dict | None:
    m = IMG_RE.match(img)
    if not m:
        return None
    return {
        "wit": int(m.group(1)),
        "digit_type": m.group(2),
        "digit": int(m.group(3)),
        "page": int(m.group(4)),
        "bbox": m.group(5),
    }


class Command(BaseCommand):
    help = "Migrate RegionPair data: reorder pairs, backfill digit_1/digit_2, validate"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Analyze and report without writing",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=50_000,
            help="Rows per UPDATE batch",
        )
        parser.add_argument(
            "--report",
            type=str,
            default="migration_report.json",
            help="Output file for the migration report",
        )
        parser.add_argument(
            "--skip-reorder",
            action="store_true",
            help="Skip reorder step (if already done)",
        )
        parser.add_argument(
            "--skip-backfill",
            action="store_true",
            help="Skip backfill, only run validation",
        )

    def handle(self, *args, **options):
        stats = defaultdict(int)
        issues = []

        if not options["skip_reorder"]:
            self._reorder(options, stats, issues)

        if not options["skip_backfill"]:
            self._backfill(options, stats, issues)

        self._validate(stats, issues)
        self._report(options["report"], stats, issues)
        self._print_summary(stats, options["dry_run"])

    # ──────────────────────────────────────────────
    # Phase 0: Reorder pairs (sort_key → alphabetical)
    # ──────────────────────────────────────────────

    def _reorder(self, options, stats, issues):
        self.stdout.write("Checking for misordered pairs (sort_key → alphabetical)...")

        with connection.cursor() as c:
            c.execute("SELECT count(*) FROM webapp_regionpair WHERE img_1 > img_2")
            count = c.fetchone()[0]

        stats["misordered_before"] = count
        if count == 0:
            self.stdout.write("  no misordered pairs found.")
            return

        self.stdout.write(
            self.style.WARNING(
                f"  {count} pairs where img_1 > img_2 (alphabetical) — need swap"
            )
        )

        if options["dry_run"]:
            stats["would_reorder"] = count
            return

        batch_size = options["batch_size"]
        total = 0
        while True:
            with connection.cursor() as c:
                # Swap img_1↔img_2, regions_id_1↔regions_id_2, digit_1↔digit_2, anno_1↔anno_2
                c.execute(
                    """
                    UPDATE webapp_regionpair
                    SET img_1 = img_2, img_2 = img_1,
                        regions_id_1 = regions_id_2, regions_id_2 = regions_id_1,
                        digit_1 = digit_2, digit_2 = digit_1,
                        anno_1 = anno_2, anno_2 = anno_1
                    WHERE id IN (
                        SELECT id FROM webapp_regionpair
                        WHERE img_1 > img_2
                        LIMIT %s
                    )
                """,
                    [batch_size],
                )
                affected = c.rowcount

            total += affected
            self.stdout.write(f"  reordered {total}/{count}...")
            if affected < batch_size:
                break

        stats["reordered"] = total

    # ──────────────────────────────────────────────
    # Phase 1: Backfill digit_1/digit_2 from img names
    # ──────────────────────────────────────────────

    def _backfill(self, options, stats, issues):
        dry_run = options["dry_run"]
        batch_size = options["batch_size"]

        remaining = RegionPair.objects.filter(digit_1__isnull=True).count()
        stats["to_backfill"] = remaining

        if remaining == 0:
            self.stdout.write(
                "Nothing to backfill — digit_1/digit_2 already populated."
            )
            return

        self.stdout.write(f"Backfilling {remaining} rows (batch_size={batch_size})...")

        if dry_run:
            self._backfill_dry_run(batch_size, stats, issues)
        else:
            self._backfill_apply(batch_size, stats, issues)

    def _backfill_dry_run(self, batch_size, stats, issues):
        qs = (
            RegionPair.objects.filter(digit_1__isnull=True)
            .only("id", "img_1", "img_2")
            .order_by("id")
        )
        for i, pair in enumerate(qs.iterator(chunk_size=batch_size)):
            if (i + 1) % 50_000 == 0:
                self.stdout.write(f"  scanned {i + 1}...")

            ref1 = parse_img(pair.img_1)
            ref2 = parse_img(pair.img_2)

            if not ref1 or not ref2:
                stats["parse_errors"] += 1
                issues.append(
                    {
                        "pair_id": pair.id,
                        "type": "parse_error",
                        "img_1": pair.img_1,
                        "img_2": pair.img_2,
                        "detail": f"{'img_1' if not ref1 else 'img_2'} does not match expected pattern",
                    }
                )
                continue

            stats["would_backfill"] += 1

    def _backfill_apply(self, batch_size, stats, issues):
        # Flag unparseable rows
        self.stdout.write("  checking for unparseable image names...")
        unparseable = list(
            RegionPair.objects.filter(digit_1__isnull=True)
            .extra(
                where=[
                    r"img_1 !~ '^wit\d+_\w{3}\d+_\d+' OR img_2 !~ '^wit\d+_\w{3}\d+_\d+'"
                ]
            )
            .values_list("id", "img_1", "img_2")[:1000]
        )
        if unparseable:
            stats["parse_errors"] = len(unparseable)
            for pid, img1, img2 in unparseable:
                issues.append(
                    {
                        "pair_id": pid,
                        "type": "parse_error",
                        "img_1": img1,
                        "img_2": img2,
                    }
                )
            self.stdout.write(
                self.style.WARNING(
                    f"  {len(unparseable)} rows with unparseable names (skipped)"
                )
            )

        total = 0
        while True:
            with connection.cursor() as c:
                c.execute(
                    """
                    UPDATE webapp_regionpair
                    SET digit_1 = (regexp_matches(img_1, '_\\w{3}(\\d+)_'))[1]::int,
                        digit_2 = (regexp_matches(img_2, '_\\w{3}(\\d+)_'))[1]::int
                    WHERE id IN (
                        SELECT id FROM webapp_regionpair
                        WHERE digit_1 IS NULL
                          AND img_1 ~ '^wit\\d+_\\w{3}\\d+_\\d+'
                          AND img_2 ~ '^wit\\d+_\\w{3}\\d+_\\d+'
                        LIMIT %s
                    )
                """,
                    [batch_size],
                )
                affected = c.rowcount

            total += affected
            self.stdout.write(f"  backfilled {total} rows...")
            if affected < batch_size:
                break

        stats["backfilled"] = total

    # ──────────────────────────────────────────────
    # Phase 2: Validate
    # ──────────────────────────────────────────────

    def _validate(self, stats, issues):
        self.stdout.write("\nValidating consistency...")

        # 2a. Remaining NULLs
        nulls = RegionPair.objects.filter(digit_1__isnull=True).count()
        stats["remaining_nulls"] = nulls
        if nulls:
            self.stdout.write(
                self.style.WARNING(f"  {nulls} rows still have NULL digit_1")
            )

        # 2b. Cross-check digit_* against regions_id_* via Regions table
        self.stdout.write("  cross-checking digit vs regions_id...")
        regions_to_digit = dict(
            Regions.objects.select_related("digitization").values_list(
                "id", "digitization_id"
            )
        )
        stats["regions_mapped"] = len(regions_to_digit)

        mismatch_count = 0
        sample_limit = 500

        qs = (
            RegionPair.objects.filter(digit_1__isnull=False)
            .only(
                "id",
                "img_1",
                "img_2",
                "digit_1",
                "digit_2",
                "regions_id_1",
                "regions_id_2",
            )
            .order_by("id")
        )

        for pair in qs.iterator(chunk_size=50_000):
            expected_1 = regions_to_digit.get(pair.regions_id_1)
            expected_2 = regions_to_digit.get(pair.regions_id_2)

            mismatch_1 = expected_1 is not None and expected_1 != pair.digit_1
            mismatch_2 = expected_2 is not None and expected_2 != pair.digit_2

            if mismatch_1 or mismatch_2:
                mismatch_count += 1
                if (
                    len([i for i in issues if i.get("type") == "rid_mismatch"])
                    < sample_limit
                ):
                    issues.append(
                        {
                            "pair_id": pair.id,
                            "type": "rid_mismatch",
                            "digit_1": pair.digit_1,
                            "regions_id_1": pair.regions_id_1,
                            "rid_1_digit": expected_1,
                            "digit_2": pair.digit_2,
                            "regions_id_2": pair.regions_id_2,
                            "rid_2_digit": expected_2,
                        }
                    )

        stats["rid_mismatches"] = mismatch_count
        if mismatch_count:
            self.stdout.write(
                self.style.WARNING(
                    f"  {mismatch_count} rows where digit_* != digitization from regions_id_*\n"
                    f"  (confirms pre-existing bugs the new schema eliminates)"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("  all digit_* values consistent with regions_id_*")
            )

        # 2c. Ordering constraint
        with connection.cursor() as c:
            c.execute("SELECT count(*) FROM webapp_regionpair WHERE img_1 > img_2")
            misordered = c.fetchone()[0]
        stats["misordered_after"] = misordered
        if misordered:
            self.stdout.write(
                self.style.ERROR(f"  {misordered} rows STILL have img_1 > img_2")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("  all pairs correctly ordered (img_1 <= img_2)")
            )

    # ──────────────────────────────────────────────
    # Reporting
    # ──────────────────────────────────────────────

    def _report(self, output_file, stats, issues):
        report = {
            "generated_at": datetime.now().isoformat(),
            "stats": dict(stats),
            "issues_count": len(issues),
            "issues_by_type": {
                t: len([i for i in issues if i.get("type") == t])
                for t in {i.get("type") for i in issues}
            },
            "issues": issues,
        }
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)

        self.stdout.write(f"\nReport written to {output_file}")

    def _print_summary(self, stats, dry_run):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(
            self.style.SUCCESS("MIGRATION SUMMARY" + (" (DRY RUN)" if dry_run else ""))
        )
        self.stdout.write("=" * 60)
        for key, value in sorted(stats.items()):
            style = self.style.WARNING if "error" in key or "mismatch" in key else str
            self.stdout.write(f"  {key}: {style(str(value))}")
        self.stdout.write("=" * 60)
