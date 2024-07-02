# Generated by Django 4.0.4 on 2024-06-19 08:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("webapp", "0005_regions_rename_anno_ref_1_regionpair_regions_ref_1_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="regions",
            options={"verbose_name": "Regions", "verbose_name_plural": "Regions"},
        ),
        migrations.AlterField(
            model_name="regions",
            name="digitization",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="regions",
                to="webapp.digitization",
                verbose_name="Digitization",
            ),
        ),
    ]