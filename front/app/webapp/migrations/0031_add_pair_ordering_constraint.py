# 0031_add_pair_ordering_constraint.py
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("webapp", "0030_reorder_pairs_alphabetically"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="regionpair",
            constraint=models.CheckConstraint(
                condition=models.Q(("img_1__lte", models.F("img_2"))),
                name="pair_ordering",
            ),
        ),
    ]
