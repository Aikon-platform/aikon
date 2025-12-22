import re

from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError

from app.similarity.models.region_pair import RegionPair
from app.webapp.models.digitization import Digitization
from app.webapp.models.regions import Regions

# RUN WITH: front/venv/bin/python front/manage.py clean_regionpairs


class Command(BaseCommand):
    help = "Correct incorrect RegionPair entries in the database"

    def handle(self, *args, **options):
        stats = {
            "total_pairs": 0,
            "fixed_jpg_extension": 0,
            "fixed_region_ids": 0,
            "swapped_regions": 0,
            "swapped_alphabetical": 0,
            "score_zero": 0,
            "deleted_pairs": 0,
            "errors": 0,
            "duplicates_found": 0,
            "ids_to_delete": [],
        }

        # Create regions_to_digit mapping once
        self.stdout.write("Building regions-to-digitization mapping...")
        regions_to_digit = {}
        for region in Regions.objects.select_related("digitization").all():
            if region.digitization:
                regions_to_digit[region.id] = region.digitization.id
        self.stdout.write(f"Mapped {len(regions_to_digit)} regions")

        pairs = RegionPair.objects.all()
        total = pairs.count()
        self.stdout.write(f"\nProcessing {total} RegionPairs...\n")

        for i, pair in enumerate(pairs):
            stats["total_pairs"] += 1

            if (i + 1) % 100 == 0:
                self.stdout.write(f"Progress: {i + 1}/{total}")

            try:
                self._process_pair(pair, stats, regions_to_digit)
            except Exception as e:
                stats["errors"] += 1
                self.stdout.write(
                    self.style.ERROR(f"Error with RegionPair #{pair.id}: {e}")
                )

        self._find_duplicates(stats)
        self._print_summary(stats)

    def _process_pair(self, pair, stats, regions_to_digit):
        """Process a single RegionPair using the model's clean() method"""
        changes_made = False
        pair_id = pair.id

        # Store original values to detect changes
        original = (pair.img_1, pair.img_2, pair.regions_id_1, pair.regions_id_2)

        # Apply clean() to normalize and validate
        try:
            pair.clean(regions_to_digit=regions_to_digit, create_missing_regions=True)
        except ValidationError as e:
            self.stdout.write(
                self.style.ERROR(f"Pair #{pair_id}: Validation failed - {e}")
            )
            stats["errors"] += 1
            stats["ids_to_delete"].append(pair_id)
            return

        # Track what clean() fixed
        current = (pair.img_1, pair.img_2, pair.regions_id_1, pair.regions_id_2)
        if current != original:
            changes_made = True

            # Log specific changes for stats
            if original[0] != current[0] or original[1] != current[1]:
                if not original[0].endswith(".jpg") or not original[1].endswith(".jpg"):
                    stats["fixed_jpg_extension"] += 1

                if original[0] != current[0]:  # Images were swapped
                    stats["swapped_alphabetical"] += 1

            if (original[2], original[3]) != (current[2], current[3]):
                if original[2] == current[3] and original[3] == current[2]:
                    stats["swapped_regions"] += 1
                else:
                    stats["fixed_region_ids"] += 1

        # Handle score == 0
        if pair.score == 0:
            self.stdout.write(
                self.style.WARNING(f"Pair #{pair_id}: Score is zero, setting to None")
            )
            pair.score = None
            stats["score_zero"] += 1
            changes_made = True

        # Check for duplicates
        if changes_made:
            existing = (
                RegionPair.objects.filter(img_1=pair.img_1, img_2=pair.img_2)
                .exclude(id=pair_id)
                .first()
            )

            if existing:
                self.stdout.write(
                    self.style.WARNING(
                        f"Pair #{pair_id}: Would create duplicate with #{existing.id}. "
                        f"Merging into existing pair..."
                    )
                )

                # Merge data into existing pair
                if pair.score and (not existing.score or pair.score > existing.score):
                    existing.score = pair.score

                if pair.category and not existing.category:
                    existing.category = pair.category

                if pair.is_manual and not existing.is_manual:
                    existing.is_manual = True

                if pair.category_x:
                    existing.category_x = list(
                        set(existing.category_x + pair.category_x)
                    )

                existing.save()

                # Delete duplicate
                pair.delete()
                stats["duplicates_found"] += 1
                stats["deleted_pairs"] += 1
                self.stdout.write(f"  - Deleted duplicate pair #{pair_id}")
                return

        # Save changes
        if changes_made:
            pair.save()

    def _find_duplicates(self, stats):
        """Find and report duplicate pairs"""
        self.stdout.write("\nLooking for duplicates...")

        # Find all unique combinations
        all_pairs = RegionPair.objects.values_list(
            "img_1", "img_2", "regions_id_1", "regions_id_2", "id"
        )

        seen = {}
        duplicates = []

        for img_1, img_2, r_id_1, r_id_2, pair_id in all_pairs:
            key = (img_1, img_2, r_id_1, r_id_2)

            if key in seen:
                duplicates.append((pair_id, seen[key]))
            else:
                seen[key] = pair_id

        # Report duplicates
        if duplicates:
            self.stdout.write(
                self.style.WARNING(f"\nFound {len(duplicates)} duplicate pairs:")
            )
            for dup_id, original_id in duplicates[:10]:  # Show first 10
                self.stdout.write(
                    f"  - Pair #{dup_id} is a duplicate of #{original_id}"
                )

            if len(duplicates) > 10:
                self.stdout.write(f"  ... and {len(duplicates) - 10} more")

            self.stdout.write("\nTo remove duplicates, you can run:")
            self.stdout.write(
                "  RegionPair.objects.filter(id__in=[...duplicate_ids...]).delete()"
            )
            stats["ids_to_delete"].extend(dup[0] for dup in duplicates)

    def _print_summary(self, stats):
        """Print summary statistics"""
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("CORRECTION SUMMARY"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"Total pairs processed:     {stats['total_pairs']}")
        self.stdout.write(f"Fixed .jpg extensions:     {stats['fixed_jpg_extension']}")
        self.stdout.write(f"Fixed invalid region IDs:  {stats['fixed_region_ids']}")
        self.stdout.write(f"Fixed alphabetical order:  {stats['swapped_alphabetical']}")
        self.stdout.write(f"Score set to None:         {stats['score_zero']}")
        self.stdout.write(f"Fixed swapped regions:     {stats['swapped_regions']}")
        self.stdout.write(f"Duplicates found:          {stats['duplicates_found']}")
        self.stdout.write(f"Deleted pairs:             {stats['deleted_pairs']}")
        self.stdout.write(f"Errors encountered:        {stats['errors']}")
        self.stdout.write("=" * 60)

        total_fixes = (
            stats["fixed_jpg_extension"]
            + stats["fixed_region_ids"]
            + stats["swapped_regions"]
        )

        if stats["ids_to_delete"]:
            self.stdout.write(
                self.style.ERROR(
                    f"\n⚠️ The following pairs have invalid digitizations and should be deleted: {stats['ids_to_delete']}"
                )
            )

        if total_fixes > 0:
            self.stdout.write(
                self.style.SUCCESS(f"\n✓ Fixed {total_fixes} issues total")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("\n✓ No issues found - database is clean!")
            )
