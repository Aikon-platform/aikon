from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("webapp", "0026_alter_series_shared_with"),
    ]

    # NOTE the three consecutive migrations should be applied at once
    # The first one (0029) adds the new fields, updates indexes, and removes the ordering constraint
    # The second one (0030) fills the new fields and reorders the img pairs alphabetically
    # The third one (0031) apply new ordering constraint

    operations = [
        migrations.RemoveIndex(
            model_name="regionpair", name="webapp_regi_regions_23ea83_idx"
        ),
        migrations.RemoveIndex(
            model_name="regionpair", name="webapp_regi_regions_8f0f96_idx"
        ),
        migrations.RemoveIndex(
            model_name="regionpair", name="webapp_regi_regions_96cfbb_idx"
        ),
        migrations.RemoveIndex(
            model_name="regionpair", name="webapp_regi_regions_defc04_idx"
        ),
        migrations.RemoveIndex(model_name="regionpair", name="idx_same_regions"),
        migrations.RemoveIndex(
            model_name="regionpair", name="webapp_regi_img_1_685841_idx"
        ),
        migrations.RemoveIndex(
            model_name="regionpair", name="webapp_regi_img_2_c47c92_idx"
        ),
        migrations.AddField(
            model_name="regionpair",
            name="anno_1",
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AddField(
            model_name="regionpair",
            name="anno_2",
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AddField(
            model_name="regionpair",
            name="digit_1",
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name="regionpair",
            name="digit_2",
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name="regionpair",
            name="regions_id_1",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="regionpair",
            name="regions_id_2",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddIndex(
            model_name="regionpair",
            index=models.Index(
                fields=["digit_1", "digit_2"], name="webapp_regi_digit_1_0a044c_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="regionpair",
            index=models.Index(
                fields=["digit_1", "digit_2", "score"],
                name="webapp_regi_digit_1_19fd9f_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="regionpair",
            index=models.Index(
                fields=["img_1", "img_2"], name="webapp_regi_img_1_55f282_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="regionpair",
            index=models.Index(fields=["img_1"], name="webapp_regi_img_1_new_idx"),
        ),
        migrations.AddIndex(
            model_name="regionpair",
            index=models.Index(fields=["img_2"], name="webapp_regi_img_2_new_idx"),
        ),
        migrations.AddIndex(
            model_name="regionpair",
            index=models.Index(
                fields=["category"], name="webapp_regi_categor_eadd25_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="regionpair",
            index=models.Index(
                condition=models.Q(("digit_1", models.F("digit_2"))),
                fields=["digit_1", "digit_2"],
                name="idx_same_digit",
            ),
        ),
    ]
