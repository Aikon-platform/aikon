from typing import List, Tuple

from django.core.management.base import BaseCommand
from django.db.models.expressions import RawSQL
from django.db.models import Q
from django.db import connection

from app.webapp.models.witness import Witness


class Command(BaseCommand):
    help = "Update Witness.json by moving the contents of the field 'regions' to 'region_extraction'"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--limit", type=int, default=None)

    def handle(self, *args, **opts):
        # to optimise, we compute a mapping of witness id to region extraction ids in raw sql
        sql = """
            SELECT webapp_witness.id, array_agg(webapp_regionextraction.id) AS regionextraction_id
            FROM webapp_witness
            JOIN webapp_digitization ON webapp_witness.id = webapp_digitization.witness_id
            JOIN webapp_regionextraction ON webapp_digitization.id = webapp_regionextraction.digitization_id
            GROUP BY webapp_witness.id;
        """
        with connection.cursor() as cursor:
            cursor.execute(sql)
            # list of [ <witness id>, [<region ids>] ]
            witness_regions = cursor.fetchall()
            # dict: { <witness id>: [<region ids>] }
            witness_regions = {
                wit_id: region_extraction_ids
                for (wit_id, region_extraction_ids) in witness_regions
            }

        qs = Witness.objects.exclude(Q(json__regions__isnull=True))
        if opts["limit"]:
            qs = qs[: opts["limit"]]

        stats = {"ok": 0, "skip": 0, "fail": 0, "total": 0}
        to_update = []
        for wit in qs.iterator(chunk_size=50):
            try:
                region_extraction_ids = witness_regions.get(wit.id, [])
                wit_json = wit.json or wit.to_json()

                if "regions" in wit_json.keys():
                    del wit_json["regions"]

                # if wit_json["region_extraction"] is up to date, skip this row
                if len(region_extraction_ids) == len(
                    wit_json.get("region_extraction", [])
                ):
                    stats["skip"] += 1
                    continue

                wit_json["region_extraction"] = region_extraction_ids
                wit.json = wit_json
                to_update.append(wit)
                stats["ok"] += 1

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"error on witness #{wit.id}: {e}"))
                stats["fail"] += 1
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
