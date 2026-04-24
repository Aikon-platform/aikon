from django.core.management.base import BaseCommand
from django.core.cache import cache


class Command(BaseCommand):
    help = "Clear all cache"

    def add_arguments(self, parser):
        # Create a mutually exclusive group
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--regext",
            "-r",
            type=int,
            help="ID of the RegionExtraction to clear the cache",
        )
        group.add_argument(
            "--all",
            "-a",
            action="store_true",
            help="Clear all cache",
        )

    def handle(self, *args, **options):
        region_extraction_id = options.get("regext")
        process_all = options.get("all")

        if region_extraction_id:
            cache_key = f"regions_q_imgs_{region_extraction_id}"
            cache.delete(cache_key)
            self.style.SUCCESS(f"regions_q_imgs_{region_extraction_id} cache cleared!")
        elif process_all:
            cache.clear()
            self.style.SUCCESS("All cache cleared!")
