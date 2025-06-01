import re

from django.core.management.base import BaseCommand

from app.similarity.models.region_pair import RegionPair
from app.webapp.models.digitization import Digitization

# RUN WITH: front/venv/bin/python front/manage.py clean_regionpairs


def get_digit_id(img):
    """Extract the digitization ID from the image filename
    img names follow this template "wit<id>_<digit><id>_<nb>.jpg".
    e.g. wit56_pdf78_0012.jpg -> digitization ID is 78"""
    return int(re.findall(r"\d+", img)[1])


class Command(BaseCommand):
    help = "Correct incorrect RegionPair entries in the database"

    def handle(self, *args, **options):
        # Statistics
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

        pairs = RegionPair.objects.all()
        total = pairs.count()
        self.stdout.write(f"\nProcessing {total} RegionPairs...\n")

        for i, pair in enumerate(pairs):
            stats["total_pairs"] += 1

            if (i + 1) % 100 == 0:
                self.stdout.write(f"Progress: {i + 1}/{total}")

            try:
                self._process_pair(pair, stats)
            except Exception as e:
                stats["errors"] += 1
                self.stdout.write(
                    self.style.ERROR(f"Error with RegionPair #{pair.id}: {e}")
                )

        self._find_duplicates(stats)

        self._print_summary(stats)

    def _process_pair(self, pair, stats):
        """Process a single RegionPair"""
        changes_made = False
        pair_id = pair.id

        # Fix missing .jpg extension
        if not pair.img_1.endswith(".jpg"):
            pair.img_1 = f"{pair.img_1}.jpg"
            stats["fixed_jpg_extension"] += 1
            changes_made = True

        if not pair.img_2.endswith(".jpg"):
            pair.img_2 = f"{pair.img_2}.jpg"
            stats["fixed_jpg_extension"] += 1
            changes_made = True

        def sort_key(s):
            return [
                int(part) if part.isdigit() else part for part in re.split("(\d+)", s)
            ]

        # Check if images need to be swapped for alphabetical order
        sorted_imgs = sorted([pair.img_1, pair.img_2], key=sort_key)
        if [pair.img_1, pair.img_2] != sorted_imgs:
            self.stdout.write(
                self.style.WARNING(
                    f"Pair #{pair.id}: Images not in alphabetical order. "
                    f"Swapping {pair.img_1} <-> {pair.img_2}"
                )
            )
            # Swap images and their corresponding regions
            pair.img_1, pair.img_2 = pair.img_2, pair.img_1
            pair.regions_id_1, pair.regions_id_2 = pair.regions_id_2, pair.regions_id_1
            stats["swapped_alphabetical"] += 1
            changes_made = True

        digit_id_1 = get_digit_id(pair.img_1)
        digit_id_2 = get_digit_id(pair.img_2)

        # check if duplicates would be created by the img name update
        if changes_made:
            existing = (
                RegionPair.objects.filter(img_1=pair.img_1, img_2=pair.img_2)
                .exclude(id=pair.id)
                .first()
            )

            if existing:
                self.stdout.write(
                    self.style.WARNING(
                        f"Pair #{pair.id}: Would create duplicate with #{existing.id}. "
                        f"Merging into existing pair..."
                    )
                )

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

                # Delete the duplicate
                pair.delete()
                stats["duplicates_found"] += 1
                stats["deleted_pairs"] += 1
                self.stdout.write(f"  - Deleted duplicate pair #{pair_id}")
                return  # Skip the rest of processing for this pair

        if not digit_id_1 or not digit_id_2:
            self.stdout.write(
                self.style.ERROR(
                    f"Pair #{pair_id}: Could not extract digit IDs from img names"
                )
            )
            stats["ids_to_delete"].append(pair_id)
            # TODO delete?
            return

        # Check if scores are zero
        if pair.score == 0:
            self.stdout.write(
                self.style.WARNING(f"Pair #{pair.id}: Score is zero, setting to None")
            )
            pair.score = None
            stats["score_zero"] += 1
            changes_made = True

        # Get valid region IDs for each digitization
        try:
            digit_1 = Digitization.objects.get(id=digit_id_1)
            valid_regions_1 = list(digit_1.get_regions().values_list("id", flat=True))
        except Digitization.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f"Pair #{pair.id}: Digitization {digit_id_1} not found"
                )
            )
            stats["ids_to_delete"].append(pair_id)
            # TODO delete? check for other witness digitizations?
            return

        try:
            digit_2 = Digitization.objects.get(id=digit_id_2)
            valid_regions_2 = list(digit_2.get_regions().values_list("id", flat=True))
        except Digitization.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f"Pair #{pair.id}: Digitization {digit_id_2} not found"
                )
            )
            stats["ids_to_delete"].append(pair_id)
            # TODO delete? check for other witness digitizations?
            return

        # Check if regions are swapped
        if (
            pair.regions_id_1 not in valid_regions_1
            and pair.regions_id_2 not in valid_regions_2
            and pair.regions_id_1 in valid_regions_2
            and pair.regions_id_2 in valid_regions_1
        ):
            self.stdout.write(
                self.style.WARNING(f"Pair #{pair.id}: Regions are swapped! Fixing...")
            )
            pair.regions_id_1, pair.regions_id_2 = pair.regions_id_2, pair.regions_id_1
            stats["swapped_regions"] += 1
            changes_made = True

        # Fix invalid region IDs
        else:
            if pair.regions_id_1 not in valid_regions_1:
                self.stdout.write(
                    self.style.WARNING(
                        f"Pair #{pair.id}: regions_id_1 ({pair.regions_id_1}) not valid."
                        f"Using first valid region: {valid_regions_1[0]}"
                    )
                )
                pair.regions_id_1 = valid_regions_1[0]
                stats["fixed_region_ids"] += 1
                changes_made = True

            if pair.regions_id_2 not in valid_regions_2:
                self.stdout.write(
                    self.style.WARNING(
                        f"Pair #{pair.id}: regions_id_2 ({pair.regions_id_2}) not valid."
                        f"Using first valid region: {valid_regions_2[0]}"
                    )
                )
                pair.regions_id_2 = valid_regions_2[0]
                stats["fixed_region_ids"] += 1
                changes_made = True

        # Save if we made changes
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
                stats["duplicates_found"] += 1
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
