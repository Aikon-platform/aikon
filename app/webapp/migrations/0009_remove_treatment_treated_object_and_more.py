# Generated by Django 4.0.4 on 2024-07-04 08:17

from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("webapp", "0008_alter_conservationplace_options_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="treatment",
            name="treated_object",
        ),
        migrations.RemoveField(
            model_name="treatment",
            name="treatment_type",
        ),
        migrations.RemoveField(
            model_name="treatment",
            name="user_id",
        ),
        migrations.AddField(
            model_name="treatment",
            name="api_tracking_id",
            field=models.UUIDField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name="treatment",
            name="is_finished",
            field=models.BooleanField(default=False, editable=False),
        ),
        migrations.AddField(
            model_name="treatment",
            name="notify_email",
            field=models.BooleanField(
                blank=True,
                default=True,
                help_text="Send an email when the task is finished",
                verbose_name="Notify by email",
            ),
        ),
        migrations.AddField(
            model_name="treatment",
            name="requested_by",
            field=models.ForeignKey(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="treatment",
            name="requested_on",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="treatment",
            name="treated_objects",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="treatment",
            name="status",
            field=models.CharField(default="Pending", editable=False, max_length=20),
        ),
        migrations.AlterField(
            model_name="treatment",
            name="task_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("regions", "regions"),
                    ("vectorization", "vectorization"),
                    ("similarity", "similarity"),
                ],
                max_length=50,
                null=True,
            ),
        ),
        migrations.CreateModel(
            name="DocumentSet",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=50, unique=True)),
                ("is_public", models.BooleanField(default=False)),
                (
                    "wit_ids",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.IntegerField(), default=list, size=None
                    ),
                ),
                (
                    "ser_ids",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.IntegerField(), default=list, size=None
                    ),
                ),
                (
                    "digit_ids",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.IntegerField(), default=list, size=None
                    ),
                ),
                (
                    "work_ids",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.IntegerField(), default=list, size=None
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True, null=True)),
                (
                    "user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Document set",
                "verbose_name_plural": "Document sets",
            },
        ),
        migrations.AddField(
            model_name="treatment",
            name="document_set",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="treatments",
                to="webapp.documentset",
                verbose_name="Document set",
            ),
        ),
    ]