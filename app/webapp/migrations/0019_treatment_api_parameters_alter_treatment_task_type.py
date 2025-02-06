# Generated by Django 5.1.3 on 2025-02-05 15:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("webapp", "0018_userprofile"),
    ]

    operations = [
        migrations.AddField(
            model_name="treatment",
            name="api_parameters",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="treatment",
            name="task_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("regions", "Image regions extraction"),
                    ("similarity", "Compute similarity score"),
                    ("vectorization", "Vectorization"),
                ],
                max_length=50,
                null=True,
                verbose_name="Task type",
            ),
        ),
    ]
