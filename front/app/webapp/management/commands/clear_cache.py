from django.core.management.base import BaseCommand
from django.core.cache import cache


class Command(BaseCommand):
    help = "Clear all cache"

    def add_arguments(self, parser):
        # Create a mutually exclusive group
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--regions",
            "-r",
            type=int,
            help="ID of the Regions to clear the cache",
        )
        group.add_argument(
            "--all",
            "-a",
            action="store_true",
            help="Clear all cache",
        )

    def handle(self, *args, **options):
        regions_id = options.get("regions_id")
        process_all = options.get("all")

        if regions_id:
            cache_key = f"regions_q_imgs_{regions_id}"
            cache.delete(cache_key)
            self.style.SUCCESS(f"regions_q_imgs_{regions_id} cache cleared!")
        elif process_all:
            cache.clear()
            self.style.SUCCESS("All cache cleared!")
