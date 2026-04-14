import re
from django.db import migrations

IMG_RE = re.compile(r"^wit(\d+)_(\w{3})(\d+)_(\d+)(?:_([\d,]+))?\.jpg$")


def parse_img(img):
    m = IMG_RE.match(img)
    if m:
        return int(m.group(3))
    return None


def reorder_pairs(apps, schema_editor):
    RegionPair = apps.get_model("webapp", "RegionPair")

    batch_size = 5000
    updated = []

    for pair in RegionPair.objects.all().iterator(chunk_size=batch_size):
        needs_swap = pair.img_2 < pair.img_1

        if needs_swap:
            pair.img_1, pair.img_2 = pair.img_2, pair.img_1
            pair.regions_id_1, pair.regions_id_2 = pair.regions_id_2, pair.regions_id_1
            pair.anno_1, pair.anno_2 = pair.anno_2, pair.anno_1

        # Extract digit_1 and digit_2
        pair.digit_1 = parse_img(pair.img_1)
        pair.digit_2 = parse_img(pair.img_2)

        updated.append(pair)

        if len(updated) >= batch_size:
            RegionPair.objects.bulk_update(
                updated,
                [
                    "img_1",
                    "img_2",
                    "regions_id_1",
                    "regions_id_2",
                    "anno_1",
                    "anno_2",
                    "digit_1",
                    "digit_2",
                ],
                batch_size=batch_size,
            )
            updated = []

    if updated:
        RegionPair.objects.bulk_update(
            updated,
            [
                "img_1",
                "img_2",
                "regions_id_1",
                "regions_id_2",
                "anno_1",
                "anno_2",
                "digit_1",
                "digit_2",
            ],
            batch_size=batch_size,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("webapp", "0030_remove_region_id_in_regionpair_and_more"),
    ]

    operations = [
        migrations.RunPython(reorder_pairs, reverse_code=migrations.RunPython.noop),
    ]
