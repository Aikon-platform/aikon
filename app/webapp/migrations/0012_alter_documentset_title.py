# Generated by Django 4.0.4 on 2024-07-30 13:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("webapp", "0011_alter_content_work_alter_documentset_digit_ids_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="documentset",
            name="title",
            field=models.CharField(max_length=50),
        ),
    ]