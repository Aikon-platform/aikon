# Generated by Django 4.0.4 on 2024-08-05 12:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("webapp", "0013_alter_conservationplace_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="documentset",
            name="selection",
            field=models.JSONField(
                blank=True, null=True, verbose_name="JSON selection"
            ),
        ),
        migrations.AddField(
            model_name="documentset",
            name="json",
            field=models.JSONField(
                blank=True, null=True, verbose_name="JSON representation"
            ),
        ),
        migrations.AddField(
            model_name="series",
            name="json",
            field=models.JSONField(
                blank=True, null=True, verbose_name="JSON representation"
            ),
        ),
        migrations.AddField(
            model_name="treatment",
            name="json",
            field=models.JSONField(
                blank=True, null=True, verbose_name="JSON representation"
            ),
        ),
        migrations.AddField(
            model_name="witness",
            name="json",
            field=models.JSONField(
                blank=True, null=True, verbose_name="JSON representation"
            ),
        ),
        migrations.AddField(
            model_name="work",
            name="json",
            field=models.JSONField(
                blank=True, null=True, verbose_name="JSON representation"
            ),
        ),
        migrations.AlterField(
            model_name="treatment",
            name="requested_on",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AlterField(
            model_name="treatment",
            name="status",
            field=models.CharField(
                choices=[
                    ("CANCELLED", "CANCELLED"),
                    ("ERROR", "ERROR"),
                    ("IN PROGRESS", "IN PROGRESS"),
                    ("PENDING", "PENDING"),
                    ("STARTED", "STARTED"),
                    ("SUCCESS", "SUCCESS"),
                ],
                default="PENDING",
                max_length=50,
            ),
        ),
    ]
