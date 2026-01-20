import json
import sqlite3
import tempfile
from datetime import datetime
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from django.db import transaction

from app.similarity.models.region_pair import RegionPair, add_jpg
from app.webapp.models.regions import Regions


# TODO remove when all pairs are migrated
LEGACY_HASH = "e2596a98"
REPLACEMENT_HASH = "20099ddb"


def fix_img_format(img: str) -> tuple[str, bool]:
    """Fix image format, return (fixed_img, was_changed)"""
    img = add_jpg(img)
    if "_wit" in img:
        return "wit" + img.split("_wit", 1)[1], True
    return img, False


class Action:
    UPDATE = "update"
    DELETE = "delete"
    FLAG = "flag"
    MERGE = "merge"  # Update survivor with merged data from deleted duplicate

    def __init__(self, action_type: str, pair_id: int, reason: str, data: dict = None):
        self.type = action_type
        self.pair_id = pair_id
        self.reason = reason
        self.data = data or {}

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "pair_id": self.pair_id,
            "reason": self.reason,
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Action":
        return cls(d["type"], d["pair_id"], d["reason"], d.get("data", {}))


class Command(BaseCommand):
    help = "Analyze and correct RegionPair entries"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Analyze only, export actions to JSON",
        )
        parser.add_argument(
            "--output",
            type=str,
            default="actions.json",
            help="Output file for dry-run actions",
        )
        parser.add_argument(
            "--apply-from-file",
            type=str,
            help="Apply actions from JSON file",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=5000,
            help="Batch size for processing",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=10000,
            help="Max pairs to process (0 for all)",
        )

    def handle(self, *args, **options):
        if options["apply_from_file"]:
            self._apply_from_file(options["apply_from_file"])
        else:
            self._analyze(options)

    def _analyze(self, options):
        dry_run = options["dry_run"]
        batch_size = options["batch_size"]
        limit = options["limit"]

        self.stdout.write("Building regions-to-digitization mapping...")
        regions_to_digit = {
            r.id: r.digitization_id
            for r in Regions.objects.select_related("digitization").only(
                "id", "digitization_id"
            )
        }
        self.stdout.write(f"Mapped {len(regions_to_digit)} regions")

        actions = []
        stats = defaultdict(int)

        queryset = RegionPair.objects.only(
            "id",
            "img_1",
            "img_2",
            "regions_id_1",
            "regions_id_2",
            "score",
            "category",
            "category_x",
            "similarity_type",
            "similarity_hash",
        ).order_by("id")
        total = queryset.count()
        if limit:
            queryset = queryset[:limit]
            total = min(total, limit)

        self.stdout.write(
            f"\nAnalyzing {total} RegionPairs (batch_size={batch_size})...\n"
        )

        # SQLite for duplicate detection
        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as tmp:
            conn = sqlite3.connect(tmp.name)
            conn.execute(
                """
                         CREATE TABLE pairs
                         (
                             pair_id         INTEGER PRIMARY KEY,
                             img_1           TEXT,
                             img_2           TEXT,
                             hash            TEXT,
                             is_low_priority INTEGER,
                             score           REAL,
                             category        INTEGER,
                             category_x      TEXT,
                             similarity_type INTEGER
                         )
                         """
            )
            conn.execute("CREATE INDEX idx_imgs ON pairs(img_1, img_2)")

            # Analyze pairs and store for duplicate detection
            for i, pair in enumerate(queryset.iterator(chunk_size=batch_size)):
                if (i + 1) % 10000 == 0:
                    self.stdout.write(f"Progress: {i + 1}/{total}")

                pair_actions, normalized = self._analyze_pair(
                    pair, stats, regions_to_digit
                )
                actions.extend(pair_actions)

                # Store normalized images for duplicate detection
                img_1, img_2 = normalized
                if img_2 < img_1:
                    img_1, img_2 = img_2, img_1

                h = pair.similarity_hash
                if h == LEGACY_HASH:
                    h = REPLACEMENT_HASH  # Use replacement for grouping
                is_low_priority = (
                    1 if (h is None or pair.similarity_hash == LEGACY_HASH) else 0
                )

                conn.execute(
                    "INSERT INTO pairs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        pair.id,
                        img_1,
                        img_2,
                        h,
                        is_low_priority,
                        pair.score,
                        pair.category,
                        json.dumps(pair.category_x or []),
                        pair.similarity_type,
                    ),
                )

            conn.commit()

            # Phase 2: Detect duplicates using SQL
            self.stdout.write("\nDetecting duplicates...")
            dup_actions = self._detect_duplicates_sql(conn, stats)
            actions.extend(dup_actions)

            conn.close()

        # Deduplicate actions by pair_id
        actions = self._deduplicate_actions(actions)

        if dry_run:
            self._export_actions(actions, options["output"], stats)
        else:
            self._apply_actions(actions, stats, regions_to_digit)

        self._print_summary(stats, dry_run)

    def _analyze_pair(
        self, pair, stats, regions_to_digit
    ) -> tuple[list[Action], tuple[str, str]]:
        """Returns (actions, (normalized_img_1, normalized_img_2))"""
        actions = []
        updates = {}

        img_1, img_2 = pair.img_1, pair.img_2
        rid_1, rid_2 = pair.regions_id_1, pair.regions_id_2

        # Fix image format
        img_1_fixed, changed_1 = fix_img_format(img_1)
        img_2_fixed, changed_2 = fix_img_format(img_2)

        if changed_1 or changed_2:
            stats["fixed_img_format"] += 1
            img_1, img_2 = img_1_fixed, img_2_fixed

        # Check/fix ordering and region IDs
        try:
            img_1, img_2, rid_1, rid_2 = RegionPair.check_order(
                img_1,
                img_2,
                rid_1,
                rid_2,
                regions_to_digit,
                create_missing_regions=False,
            )
        except ValidationError as e:
            actions.append(Action(Action.FLAG, pair.id, f"check_order failed: {e}"))
            stats["validation_errors"] += 1
            return actions, (img_1, img_2)

        # Track changes
        if img_1 != pair.img_1:
            updates["img_1"] = img_1
        if img_2 != pair.img_2:
            updates["img_2"] = img_2
        if rid_1 != pair.regions_id_1:
            updates["regions_id_1"] = rid_1
            stats["fixed_region_ids"] += 1
        if rid_2 != pair.regions_id_2:
            updates["regions_id_2"] = rid_2
            stats["fixed_region_ids"] += 1

        # Fix legacy hash
        if pair.similarity_hash == LEGACY_HASH:
            updates["similarity_hash"] = REPLACEMENT_HASH
            stats["fixed_legacy_hash"] += 1

        # Fix score == 0
        if pair.score == 0:
            updates["score"] = None
            stats["fixed_zero_score"] += 1

        if updates:
            actions.append(
                Action(
                    Action.UPDATE,
                    pair.id,
                    "normalize",
                    {"original": {"img_1": pair.img_1, "img_2": pair.img_2}, **updates},
                )
            )

        return actions, (img_1, img_2)

    def _detect_duplicates_sql(self, conn, stats) -> list[Action]:
        actions = []
        cursor = conn.cursor()

        # Find all duplicate groups (same img_1, img_2)
        cursor.execute(
            """
                       SELECT img_1, img_2, COUNT(*) as cnt
                       FROM pairs
                       GROUP BY img_1, img_2
                       HAVING cnt > 1
                       """
        )
        dup_groups = cursor.fetchall()

        for img_1, img_2, _ in dup_groups:
            cursor.execute(
                """SELECT pair_id, hash, is_low_priority, score, category, category_x, similarity_type
                   FROM pairs
                   WHERE img_1 = ?
                     AND img_2 = ?
                   ORDER BY pair_id""",
                (img_1, img_2),
            )
            entries = cursor.fetchall()

            # Group by hash
            by_hash = defaultdict(list)
            for row in entries:
                (
                    pair_id,
                    h,
                    is_low_priority,
                    score,
                    category,
                    category_x_json,
                    sim_type,
                ) = row
                category_x = json.loads(category_x_json) if category_x_json else []
                by_hash[h].append(
                    {
                        "pair_id": pair_id,
                        "is_low_priority": is_low_priority,
                        "score": score,
                        "category": category,
                        "category_x": category_x,
                        "similarity_type": sim_type,
                        "hash": h,
                    }
                )

            # Same hash duplicates: merge into first (lowest id), delete rest
            for h, group in by_hash.items():
                if len(group) > 1:
                    group.sort(key=lambda x: x["pair_id"])
                    survivor = group[0]

                    for dup in group[1:]:
                        merge_data = self._compute_merge(survivor, dup)
                        if merge_data:
                            actions.append(
                                Action(
                                    Action.MERGE,
                                    survivor["pair_id"],
                                    f"merged from duplicate #{dup['pair_id']}",
                                    merge_data,
                                )
                            )
                            # Update survivor in memory for subsequent merges
                            survivor.update(merge_data)

                        actions.append(
                            Action(
                                Action.DELETE,
                                dup["pair_id"],
                                f"duplicate same hash ({h})",
                                {"kept_pair_id": survivor["pair_id"]},
                            )
                        )
                        stats["deleted_same_hash_dup"] += 1

            # Cross-hash duplicates
            hashes = list(by_hash.keys())
            if len(hashes) < 2:
                continue

            low_priority_hashes = [
                h for h, grp in by_hash.items() if grp[0]["is_low_priority"] == 1
            ]
            high_priority_hashes = [h for h in hashes if h not in low_priority_hashes]

            # Delete low-priority if high-priority exists, merge data into high-priority survivor
            if high_priority_hashes and low_priority_hashes:
                # Pick survivor from high-priority group (lowest id)
                high_priority_pairs = [
                    p for h in high_priority_hashes for p in by_hash[h]
                ]
                high_priority_pairs.sort(key=lambda x: x["pair_id"])
                survivor = high_priority_pairs[0]

                for h in low_priority_hashes:
                    for dup in by_hash[h]:
                        merge_data = self._compute_merge(survivor, dup)
                        if merge_data:
                            actions.append(
                                Action(
                                    Action.MERGE,
                                    survivor["pair_id"],
                                    f"merged from low-priority duplicate #{dup['pair_id']}",
                                    merge_data,
                                )
                            )
                            survivor.update(merge_data)

                        actions.append(
                            Action(
                                Action.DELETE,
                                dup["pair_id"],
                                f"duplicate with better hash (current={h})",
                                {"better_hashes": high_priority_hashes},
                            )
                        )
                        stats["deleted_low_priority_dup"] += 1

            # Flag if multiple high-priority hashes (keep all, just flag)
            if len(high_priority_hashes) > 1:
                for h in high_priority_hashes:
                    for p in by_hash[h]:
                        actions.append(
                            Action(
                                Action.FLAG,
                                p["pair_id"],
                                f"multiple valid hashes for same pair: {high_priority_hashes}",
                            )
                        )
                        stats["flagged_multi_hash"] += 1

        return actions

    def _compute_merge(self, survivor: dict, duplicate: dict) -> dict | None:
        """Compute merged values. Returns dict of fields to update, or None if no changes."""
        updates = {}

        # Keep higher score
        if duplicate["score"] and (
            not survivor["score"] or duplicate["score"] > survivor["score"]
        ):
            updates["score"] = duplicate["score"]

        # Keep category if survivor doesn't have one
        if duplicate["category"] and not survivor["category"]:
            updates["category"] = duplicate["category"]

        # Merge category_x (union)
        if duplicate["category_x"]:
            merged_x = list(
                set((survivor["category_x"] or []) + duplicate["category_x"])
            )
            if merged_x != (survivor["category_x"] or []):
                updates["category_x"] = merged_x

        # Keep strongest similarity_type: MANUAL(2) > PROPAGATED(3) > AUTO(1)
        type_priority = {2: 0, 3: 1, 1: 2, None: 3}
        surv_type = survivor["similarity_type"]
        dup_type = duplicate["similarity_type"]
        if type_priority.get(dup_type, 3) < type_priority.get(surv_type, 3):
            updates["similarity_type"] = dup_type

        # Keep non-deprecated hash (already handled by grouping logic, but ensure replacement)
        if survivor["hash"] is None and duplicate["hash"]:
            updates["similarity_hash"] = duplicate["hash"]

        return updates if updates else None

    def _deduplicate_actions(self, actions: list[Action]) -> list[Action]:
        """Keep most severe action per pair_id: DELETE > UPDATE/MERGE > FLAG"""
        priority = {Action.DELETE: 0, Action.UPDATE: 1, Action.MERGE: 1, Action.FLAG: 2}
        by_pair = {}

        for action in actions:
            pid = action.pair_id
            if (
                pid not in by_pair
                or priority[action.type] < priority[by_pair[pid].type]
            ):
                by_pair[pid] = action
            elif action.type in (Action.UPDATE, Action.MERGE) and by_pair[pid].type in (
                Action.UPDATE,
                Action.MERGE,
            ):
                # Merge updates/merges together
                by_pair[pid].data.update(action.data)
                # If either is UPDATE, keep as UPDATE (it includes normalization)
                if action.type == Action.UPDATE or by_pair[pid].type == Action.UPDATE:
                    by_pair[pid].type = Action.UPDATE

        return list(by_pair.values())

    def _export_actions(self, actions: list[Action], output_file: str, stats):
        export = {
            "generated_at": datetime.now().isoformat(),
            "stats": dict(stats),
            "actions": [a.to_dict() for a in actions],
        }
        with open(output_file, "w") as f:
            json.dump(export, f, indent=2)

        self.stdout.write(
            self.style.SUCCESS(f"\nExported {len(actions)} actions to {output_file}")
        )

    def _apply_from_file(self, filepath: str):
        with open(filepath) as f:
            data = json.load(f)

        actions = [Action.from_dict(a) for a in data["actions"]]
        stats = defaultdict(int)

        self.stdout.write(f"Applying {len(actions)} actions from {filepath}...")

        # Build regions_to_digit for updates that need re-validation
        regions_to_digit = {
            r.id: r.digitization_id
            for r in Regions.objects.select_related("digitization").only(
                "id", "digitization_id"
            )
        }

        self._apply_actions(actions, stats, regions_to_digit)
        self._print_summary(stats, dry_run=False)

    def _apply_actions(self, actions: list[Action], stats, regions_to_digit):
        updates = [a for a in actions if a.type in (Action.UPDATE, Action.MERGE)]
        deletes = [a for a in actions if a.type == Action.DELETE]
        flags = [a for a in actions if a.type == Action.FLAG]

        # Apply deletions first (before updates to avoid conflicts)
        if deletes:
            delete_ids = [a.pair_id for a in deletes]
            with transaction.atomic():
                deleted, _ = RegionPair.objects.filter(id__in=delete_ids).delete()
                stats["applied_deletes"] = deleted
            self.stdout.write(f"Deleted {deleted} pairs")

        # Apply updates/merges in batches
        if updates:
            batch_size = 500
            for i in range(0, len(updates), batch_size):
                batch = updates[i : i + batch_size]
                pair_ids = [a.pair_id for a in batch]
                pairs_map = {
                    p.id: p for p in RegionPair.objects.filter(id__in=pair_ids)
                }

                to_save = []
                for action in batch:
                    pair = pairs_map.get(action.pair_id)
                    if not pair:
                        continue

                    for field, value in action.data.items():
                        if field != "original" and hasattr(pair, field):
                            setattr(pair, field, value)

                    # Re-validate ordering after image changes
                    if "img_1" in action.data or "img_2" in action.data:
                        try:
                            pair.clean(
                                regions_to_digit=regions_to_digit,
                                create_missing_regions=True,
                            )
                        except ValidationError:
                            stats["update_validation_errors"] += 1
                            continue

                    to_save.append(pair)

                with transaction.atomic():
                    RegionPair.objects.bulk_update(
                        to_save,
                        [
                            "img_1",
                            "img_2",
                            "regions_id_1",
                            "regions_id_2",
                            "score",
                            "category",
                            "category_x",
                            "similarity_type",
                            "similarity_hash",
                        ],
                    )
                stats["applied_updates"] += len(to_save)

            self.stdout.write(f"Updated {stats['applied_updates']} pairs")

        stats["flagged_pairs"] = len(flags)
        if flags:
            self.stdout.write(
                self.style.WARNING(f"Flagged {len(flags)} pairs for review")
            )

    def _print_summary(self, stats, dry_run: bool):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(
            self.style.SUCCESS("SUMMARY" + (" (DRY RUN)" if dry_run else ""))
        )
        self.stdout.write("=" * 60)

        for key, value in sorted(stats.items()):
            self.stdout.write(f"{key}: {value}")

        self.stdout.write("=" * 60)
