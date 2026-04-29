from django.core.management.base import BaseCommand
from django.db.models.expressions import RawSQL
from django.db.models import Q

from app.webapp.models.witness import Witness


class Command(BaseCommand):
    help = "Update Witness.json by moving the contents of the field 'regions' to 'region_extraction'"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--limit", type=int, default=None)

    def handle(self, *args, **opts):
        # json["regions"] is None
        qs = Witness.objects.all()
        # qs = Witness.objects.exclude(
        #    Q(json__regions__isnull=True)
        # )
        if opts["limit"]:
            qs = qs[: opts["limit"]]

        stats = {"ok": 0, "skip": 0, "fail": 0, "total": 0}
        to_update = []
        for wit in qs.iterator(chunk_size=50):
            try:
                wit_json = wit.json or wit.to_json()

                # delete wit_json["regions"]
                if "regions" in wit_json.keys():
                    del wit_json["regions"]
                # if wit_json["region_extraction"] is up to date, skip this row
                elif len(wit.get_region_extractions()) == len(
                    wit_json.get("region_extraction", [])
                ):
                    stats["skip"] += 1
                    continue

                wit_json["region_extraction"] = [
                    r.id for r in wit.get_region_extractions()
                ]
                wit.json = wit_json
                to_update.append(wit)
                stats["ok"] += 1

            except Exception as e:
                stats["fail"] += 1
                self.stdout.write(self.style.ERROR(e))
            finally:
                stats["total"] += 1

        if opts["dry_run"]:
            self.stdout.write(
                self.style.NOTICE(f"Running this command would update: {stats}")
            )
            return

        Witness.objects.bulk_update(to_update, fields=["json"], batch_size=500)
        self.stdout.write(self.style.SUCCESS(f"{stats}"))
        return
