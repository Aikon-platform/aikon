from django.core.management.base import BaseCommand
from app.webapp.models.digitization import Digitization


class Command(BaseCommand):
    help = "Fills {name, h, w} dicts into Digitization.json.imgs"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--limit", type=int, default=None)

    def handle(self, *args, **opts):
        qs = Digitization.objects.exclude(json__imgs__isnull=True)
        if opts["limit"]:
            qs = qs[: opts["limit"]]

        stats = {"ok": 0, "skip": 0, "fail": 0}
        for digit in qs.iterator(chunk_size=50):
            imgs = (digit.json or {}).get("imgs") or []
            if imgs and all(
                isinstance(i, dict) and "h" in i and "w" in i for i in imgs
            ):
                stats["skip"] += 1
                continue
            try:
                if opts["dry_run"]:
                    self.stdout.write(f"would update #{digit.id} ({len(imgs)} imgs)")
                else:
                    digit.update_imgs_json(
                        [i["name"] if isinstance(i, dict) else i for i in imgs]
                    )
                stats["ok"] += 1
            except Exception as e:
                self.stderr.write(f"#{digit.id}: {e}")
                stats["fail"] += 1

        self.stdout.write(self.style.SUCCESS(f"{stats}"))
