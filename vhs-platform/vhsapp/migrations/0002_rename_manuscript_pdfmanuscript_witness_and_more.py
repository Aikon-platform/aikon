# Generated by Django 4.0.4 on 2023-04-05 09:28

import django.core.validators
from django.db import migrations, models
import functools
import vhsapp.utils.functions


class Migration(migrations.Migration):

    dependencies = [
        ("vhsapp", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="pdfmanuscript",
            old_name="manuscript",
            new_name="witness",
        ),
        migrations.RenameField(
            model_name="pdfvolume",
            old_name="volume",
            new_name="witness",
        ),
        migrations.AlterField(
            model_name="imagemanuscript",
            name="image",
            field=models.ImageField(
                help_text="Envoyez des images jusqu'à 2 Go.",
                upload_to=functools.partial(
                    vhsapp.utils.functions.rename_file,
                    *(),
                    **{"path": "mediafiles/img"}
                ),
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=["jpg", "jpeg", "png", "tif"]
                    )
                ],
                verbose_name="Image",
            ),
        ),
        migrations.AlterField(
            model_name="imagevolume",
            name="image",
            field=models.ImageField(
                help_text="Envoyez des images jusqu'à 2 Go.",
                upload_to=functools.partial(
                    vhsapp.utils.functions.rename_file,
                    *(),
                    **{"path": "mediafiles/img"}
                ),
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=["jpg", "jpeg", "png", "tif"]
                    )
                ],
                verbose_name="Image",
            ),
        ),
        migrations.AlterField(
            model_name="pdfmanuscript",
            name="pdf",
            field=models.FileField(
                upload_to=functools.partial(
                    vhsapp.utils.functions.rename_file,
                    *(),
                    **{"path": "manuscripts/pdf"}
                ),
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=["pdf"]
                    )
                ],
                verbose_name="PDF",
            ),
        ),
        migrations.AlterField(
            model_name="pdfvolume",
            name="pdf",
            field=models.FileField(
                upload_to=functools.partial(
                    vhsapp.utils.functions.rename_file, *(), **{"path": "volumes/pdf"}
                ),
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=["pdf"]
                    )
                ],
                verbose_name="PDF",
            ),
        ),
    ]
