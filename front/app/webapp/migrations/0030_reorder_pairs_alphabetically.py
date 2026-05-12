# import re
# from django.db import migrations
#
# IMG_RE = re.compile(r"^wit(\d+)_(\w{3})(\d+)_(\d+)(?:_([\d,]+))?\.jpg$")
#
#
# def parse_img(img):
#     m = IMG_RE.match(img)
#     if m:
#         return int(m.group(3))
#     return None
#
#
# def reorder_pairs(apps, schema_editor):
#     RegionPair = apps.get_model("webapp", "RegionPair")
#
#     batch_size = 5000
#     updated = []
#     total = 0
#
#     qs = RegionPair.objects.all()
#     count = qs.count()
#     print(f"\nReordering {count} pairs...")
#
#     for pair in qs.iterator(chunk_size=batch_size):
#         needs_swap = pair.img_2 < pair.img_1
#
#         if needs_swap:
#             pair.img_1, pair.img_2 = pair.img_2, pair.img_1
#             pair.regions_id_1, pair.regions_id_2 = pair.regions_id_2, pair.regions_id_1
#             pair.anno_1, pair.anno_2 = pair.anno_2, pair.anno_1
#
#         pair.digit_1 = parse_img(pair.img_1)
#         pair.digit_2 = parse_img(pair.img_2)
#
#         updated.append(pair)
#
#         if len(updated) >= batch_size:
#             RegionPair.objects.bulk_update(
#                 updated,
#                 [
#                     "img_1",
#                     "img_2",
#                     "regions_id_1",
#                     "regions_id_2",
#                     "anno_1",
#                     "anno_2",
#                     "digit_1",
#                     "digit_2",
#                 ],
#                 batch_size=batch_size,
#             )
#             total += len(updated)
#             print(f"{total}/{count} ({100 * total // count}%)")
#             updated = []
#
#     if updated:
#         RegionPair.objects.bulk_update(
#             updated,
#             [
#                 "img_1",
#                 "img_2",
#                 "regions_id_1",
#                 "regions_id_2",
#                 "anno_1",
#                 "anno_2",
#                 "digit_1",
#                 "digit_2",
#             ],
#             batch_size=batch_size,
#         )
#         total += len(updated)
#         print(f"🍾 Migration completed: {total} pairs!")
#
#
# class Migration(migrations.Migration):
#     dependencies = [
#         ("webapp", "0029_remove_region_id_in_regionpair_and_more"),
#     ]
#
#     operations = [
#         migrations.RunPython(reorder_pairs, reverse_code=migrations.RunPython.noop),
#     ]

from django.db import migrations

FORWARD_SQL = """
UPDATE webapp_regionpair SET
    img_1 = LEAST(img_1, img_2),
    img_2 = GREATEST(img_1, img_2),
    regions_id_1 = CASE WHEN img_2 < img_1 THEN regions_id_2 ELSE regions_id_1 END,
    regions_id_2 = CASE WHEN img_2 < img_1 THEN regions_id_1 ELSE regions_id_2 END,
    anno_1 = CASE WHEN img_2 < img_1 THEN anno_2 ELSE anno_1 END,
    anno_2 = CASE WHEN img_2 < img_1 THEN anno_1 ELSE anno_2 END,
    digit_1 = (substring(LEAST(img_1, img_2) FROM 'wit\\d+_\\w{3}(\\d+)_'))::int,
    digit_2 = (substring(GREATEST(img_1, img_2) FROM 'wit\\d+_\\w{3}(\\d+)_'))::int;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("webapp", "0029_remove_region_id_in_regionpair_and_more"),
    ]

    operations = [
        migrations.RunSQL(FORWARD_SQL, reverse_sql=migrations.RunSQL.noop),
    ]
