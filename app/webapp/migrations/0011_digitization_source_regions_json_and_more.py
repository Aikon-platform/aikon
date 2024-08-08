# Generated by Django 4.0.4 on 2024-08-07 10:05

from django.db import migrations, models
import django.db.models.deletion
import django.db.models.expressions


class Migration(migrations.Migration):

    dependencies = [
        ("webapp", "0010_alter_documentset_options_digitization_source_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="regions",
            name="json",
            field=models.JSONField(
                blank=True, null=True, verbose_name="JSON representation"
            ),
        ),
        migrations.AlterField(
            model_name="regionpair",
            name="regions_id_1",
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name="regionpair",
            name="regions_id_2",
            field=models.IntegerField(),
        ),
        migrations.AddIndex(
            model_name="regionpair",
            index=models.Index(
                fields=["regions_id_1", "img_1"], name="webapp_regi_regions_96cfbb_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="regionpair",
            index=models.Index(
                fields=["regions_id_2", "img_2"], name="webapp_regi_regions_defc04_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="regionpair",
            index=models.Index(
                fields=["img_1", "regions_id_1", "regions_id_2"],
                name="webapp_regi_img_1_685841_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="regionpair",
            index=models.Index(
                fields=["img_2", "regions_id_1", "regions_id_2"],
                name="webapp_regi_img_2_c47c92_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="regionpair",
            index=models.Index(
                condition=models.Q(
                    ("regions_id_1", django.db.models.expressions.F("regions_id_2"))
                ),
                fields=["regions_id_1", "regions_id_2"],
                name="idx_same_regions",
            ),
        ),
    ]