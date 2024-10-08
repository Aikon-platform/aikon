# Generated by Django 4.0.4 on 2024-07-17 13:17

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("webapp", "0008_alter_conservationplace_options_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="regionpair",
            old_name="regions_ref_1",
            new_name="regions_id_1",
        ),
        migrations.RenameField(
            model_name="regionpair",
            old_name="regions_ref_2",
            new_name="regions_id_2",
        ),
        migrations.AddField(
            model_name="regionpair",
            name="is_manual",
            field=models.BooleanField(default=False, max_length=150, null=True),
        ),
        migrations.AddField(
            model_name="regionpair",
            name="score",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="regionpair",
            name="category",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="regionpair",
            name="category_x",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.IntegerField(), default=list, null=True, size=None
            ),
        ),
        migrations.AddIndex(
            model_name="regionpair",
            index=models.Index(fields=["img_1"], name="webapp_regi_img_1_637fec_idx"),
        ),
        migrations.AddIndex(
            model_name="regionpair",
            index=models.Index(fields=["img_2"], name="webapp_regi_img_2_ec71b6_idx"),
        ),
        migrations.AddIndex(
            model_name="regionpair",
            index=models.Index(
                fields=["regions_id_1"], name="webapp_regi_regions_23ea83_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="regionpair",
            index=models.Index(
                fields=["regions_id_2"], name="webapp_regi_regions_8f0f96_idx"
            ),
        ),
    ]
