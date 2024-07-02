# Generated by Django 4.0.4 on 2024-06-26 14:34

import app.webapp.models.content
import app.webapp.models.digitization
import app.webapp.utils.iiif.validation
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import functools


class Migration(migrations.Migration):

    dependencies = [
        ("webapp", "0007_alter_conservationplace_options_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="conservationplace",
            options={
                "verbose_name": "Conservation place",
                "verbose_name_plural": "Conservation places",
            },
        ),
        migrations.AlterModelOptions(
            name="content",
            options={"verbose_name": "Content", "verbose_name_plural": "Contents"},
        ),
        migrations.AlterModelOptions(
            name="digitization",
            options={
                "verbose_name": "Digitization",
                "verbose_name_plural": "Digitizations",
            },
        ),
        migrations.AlterModelOptions(
            name="digitizationsource",
            options={
                "verbose_name": "Digitization source",
                "verbose_name_plural": "Digitization sources",
            },
        ),
        migrations.AlterModelOptions(
            name="edition",
            options={"verbose_name": "Edition", "verbose_name_plural": "Editions"},
        ),
        migrations.AlterModelOptions(
            name="language",
            options={"verbose_name": "Language", "verbose_name_plural": "Languages"},
        ),
        migrations.AlterModelOptions(
            name="person",
            options={
                "verbose_name": "Historical actor",
                "verbose_name_plural": "Historical actors",
            },
        ),
        migrations.AlterModelOptions(
            name="place",
            options={"verbose_name": "Place", "verbose_name_plural": "Places"},
        ),
        migrations.AlterModelOptions(
            name="regionpair",
            options={
                "verbose_name": "Region pair",
                "verbose_name_plural": "Region pairs",
            },
        ),
        migrations.AlterModelOptions(
            name="regions",
            options={"verbose_name": "Regions", "verbose_name_plural": "Regions"},
        ),
        migrations.AlterModelOptions(
            name="role",
            options={"verbose_name": "Role", "verbose_name_plural": "Roles"},
        ),
        migrations.AlterModelOptions(
            name="series",
            options={"verbose_name": "Series", "verbose_name_plural": "Series"},
        ),
        migrations.AlterModelOptions(
            name="treatment",
            options={"verbose_name": "Treatment", "verbose_name_plural": "Treatments"},
        ),
        migrations.AlterModelOptions(
            name="witness",
            options={
                "ordering": ["-place"],
                "verbose_name": "Witness",
                "verbose_name_plural": "Witnesses",
            },
        ),
        migrations.AlterModelOptions(
            name="work",
            options={"verbose_name": "Work", "verbose_name_plural": "Works"},
        ),
        migrations.AlterField(
            model_name="conservationplace",
            name="city",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="webapp.place",
                verbose_name="City",
            ),
        ),
        migrations.AlterField(
            model_name="conservationplace",
            name="license",
            field=models.URLField(blank=True, null=True, verbose_name="License"),
        ),
        migrations.AlterField(
            model_name="conservationplace",
            name="name",
            field=models.CharField(max_length=200, verbose_name="Conservation place"),
        ),
        migrations.AlterField(
            model_name="content",
            name="date_max",
            field=models.IntegerField(
                blank=True, null=True, verbose_name="Maximum date"
            ),
        ),
        migrations.AlterField(
            model_name="content",
            name="date_min",
            field=models.IntegerField(
                blank=True,
                help_text="Enter a year in numeric format. Example: '1401' to '1500' to indicate the 15<sup>th</sup> century.",
                null=True,
                verbose_name="Minimum date",
            ),
        ),
        migrations.AlterField(
            model_name="content",
            name="lang",
            field=models.ManyToManyField(
                blank=True, to="webapp.language", verbose_name="Language"
            ),
        ),
        migrations.AlterField(
            model_name="content",
            name="page_max",
            field=models.CharField(
                blank=True,
                max_length=15,
                null=True,
                validators=[app.webapp.models.content.validate_page],
                verbose_name="To page/folio",
            ),
        ),
        migrations.AlterField(
            model_name="content",
            name="page_min",
            field=models.CharField(
                blank=True,
                max_length=15,
                null=True,
                validators=[app.webapp.models.content.validate_page],
                verbose_name="From page/folio",
            ),
        ),
        migrations.AlterField(
            model_name="content",
            name="place",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="webapp.place",
                verbose_name="Creation place",
            ),
        ),
        migrations.AlterField(
            model_name="content",
            name="whole_witness",
            field=models.BooleanField(
                default=False,
                help_text="Does the witness contain only this work?",
                verbose_name="Complete witness",
            ),
        ),
        migrations.AlterField(
            model_name="content",
            name="witness",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="contents",
                to="webapp.witness",
                verbose_name="Witness",
            ),
        ),
        migrations.AlterField(
            model_name="content",
            name="work",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="webapp.work",
                verbose_name="Work",
            ),
        ),
        migrations.AlterField(
            model_name="digitization",
            name="images",
            field=models.ImageField(
                blank=True,
                help_text="Send images up to 2 GB.",
                upload_to=functools.partial(
                    app.webapp.models.digitization.no_save, *(), **{}
                ),
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=["jpg", "jpeg", "png", "tif"]
                    )
                ],
                verbose_name="image",
            ),
        ),
        migrations.AlterField(
            model_name="digitization",
            name="is_open",
            field=models.BooleanField(
                default=False,
                help_text="Are the digitized images copyright-free?",
                verbose_name="Free to use",
            ),
        ),
        migrations.AlterField(
            model_name="digitization",
            name="manifest",
            field=models.URLField(
                blank=True,
                help_text="<div class='tooltip'>\n                        <i class='fa-solid fa-circle-info'></i>\n                        <span class='tooltiptext'>A manifest allow to describe and share scans with their metadata based on the IIIF standard.</span>\n                    </div>\n                    E.g.: <a href='https://gallica.bnf.fr/iiif/ark:/12148/btv1b60004321/manifest.json' target='_blank'>\n                    https://gallica.bnf.fr/iiif/ark:/12148/btv1b60004321/manifest.json</a>",
                validators=[app.webapp.utils.iiif.validation.validate_manifest],
                verbose_name="manifest",
            ),
        ),
        migrations.AlterField(
            model_name="digitization",
            name="source",
            field=models.ForeignKey(
                blank=True,
                help_text="Example: Gallica.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="webapp.digitizationsource",
                verbose_name="Digitization source",
            ),
        ),
        migrations.AlterField(
            model_name="edition",
            name="name",
            field=models.CharField(
                help_text="Name without historical value, useful to distinguish several editions sharing date and place of publication",
                max_length=500,
                verbose_name="Title",
            ),
        ),
        migrations.AlterField(
            model_name="edition",
            name="place",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="webapp.place",
                verbose_name="Publication place",
            ),
        ),
        migrations.AlterField(
            model_name="edition",
            name="publisher",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="webapp.person",
                verbose_name="Publisher",
            ),
        ),
        migrations.AlterField(
            model_name="language",
            name="lang",
            field=models.CharField(
                max_length=200, unique=True, verbose_name="Language"
            ),
        ),
        migrations.AlterField(
            model_name="person",
            name="date_max",
            field=models.IntegerField(
                blank=True, null=True, verbose_name="Maximum date"
            ),
        ),
        migrations.AlterField(
            model_name="person",
            name="date_min",
            field=models.IntegerField(
                blank=True, null=True, verbose_name="Minimum date"
            ),
        ),
        migrations.AlterField(
            model_name="person",
            name="name",
            field=models.CharField(max_length=200, unique=True, verbose_name="Name"),
        ),
        migrations.AlterField(
            model_name="place",
            name="country",
            field=models.CharField(blank=True, max_length=150, verbose_name="Country"),
        ),
        migrations.AlterField(
            model_name="place",
            name="name",
            field=models.CharField(max_length=200, unique=True, verbose_name="Name"),
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
        migrations.AlterField(
            model_name="role",
            name="content",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="roles",
                to="webapp.content",
                verbose_name="Content",
            ),
        ),
        migrations.AlterField(
            model_name="role",
            name="person",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="webapp.person",
                verbose_name="Historical actor",
            ),
        ),
        migrations.AlterField(
            model_name="role",
            name="role",
            field=models.CharField(
                blank=True,
                choices=[
                    ("pub", "publisher"),
                    ("aut", "author"),
                    ("ill", "illuminator"),
                    ("sel", "bookseller"),
                    ("cop", "copyist"),
                    ("dra", "drawer"),
                    ("eng", "engraver"),
                    ("tra", "translator"),
                ],
                max_length=150,
                verbose_name="Role",
            ),
        ),
        migrations.AlterField(
            model_name="role",
            name="series",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="roles",
                to="webapp.series",
                verbose_name="Series",
            ),
        ),
        migrations.AlterField(
            model_name="series",
            name="date_max",
            field=models.IntegerField(
                blank=True, null=True, verbose_name="Maximum date"
            ),
        ),
        migrations.AlterField(
            model_name="series",
            name="date_min",
            field=models.IntegerField(
                blank=True,
                help_text="Enter a year in numeric format. Example: '1401' to '1500' to indicate the 15<sup>th</sup> century.",
                null=True,
                verbose_name="Minimum date",
            ),
        ),
        migrations.AlterField(
            model_name="series",
            name="edition",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="webapp.edition",
                verbose_name="Edition",
            ),
        ),
        migrations.AlterField(
            model_name="series",
            name="is_public",
            field=models.BooleanField(
                default=False,
                help_text="Record details will be accessible to other users of the database.",
                verbose_name="Make it public",
            ),
        ),
        migrations.AlterField(
            model_name="series",
            name="notes",
            field=models.TextField(
                blank=True, max_length=600, verbose_name="Additional notes"
            ),
        ),
        migrations.AlterField(
            model_name="series",
            name="place",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="webapp.conservationplace",
                verbose_name="Conservation place",
            ),
        ),
        migrations.AlterField(
            model_name="series",
            name="work",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="webapp.work",
                verbose_name="Work",
            ),
        ),
        migrations.AlterField(
            model_name="treatment",
            name="treated_object",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="treatments",
                to="webapp.digitization",
                verbose_name="Digitization",
            ),
        ),
        migrations.AlterField(
            model_name="witness",
            name="edition",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="webapp.edition",
                verbose_name="Edition",
            ),
        ),
        migrations.AlterField(
            model_name="witness",
            name="id_nb",
            field=models.CharField(
                blank=True,
                max_length=150,
                null=True,
                verbose_name="Identification number",
            ),
        ),
        migrations.AlterField(
            model_name="witness",
            name="is_public",
            field=models.BooleanField(
                default=False,
                help_text="<i class='fa-solid fa-triangle-exclamation' None></i> Record details will be accessible to other users of the database.",
                verbose_name="Make it public",
            ),
        ),
        migrations.AlterField(
            model_name="witness",
            name="link",
            field=models.URLField(
                blank=True, verbose_name="External link (online catalog, etc.)"
            ),
        ),
        migrations.AlterField(
            model_name="witness",
            name="nb_pages",
            field=models.IntegerField(
                blank=True, null=True, verbose_name="Number of pages/folios"
            ),
        ),
        migrations.AlterField(
            model_name="witness",
            name="notes",
            field=models.TextField(
                blank=True, max_length=3000, verbose_name="Additional notes"
            ),
        ),
        migrations.AlterField(
            model_name="witness",
            name="page_type",
            field=models.CharField(
                choices=[("pag", "Page"), ("fol", "Folio"), ("oth", "Other")],
                default=("pag", "Page"),
                max_length=150,
                verbose_name="Pagination type",
            ),
        ),
        migrations.AlterField(
            model_name="witness",
            name="place",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="webapp.conservationplace",
                verbose_name="Conservation place",
            ),
        ),
        migrations.AlterField(
            model_name="witness",
            name="series",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="webapp.series",
                verbose_name="Series",
            ),
        ),
        migrations.AlterField(
            model_name="witness",
            name="type",
            field=models.CharField(
                choices=[
                    ("ms", "Manuscript"),
                    ("tpr", "Letterpress print"),
                    ("wpr", "Woodblock print"),
                ],
                max_length=150,
                verbose_name="Type",
            ),
        ),
        migrations.AlterField(
            model_name="witness",
            name="volume_nb",
            field=models.IntegerField(
                blank=True,
                help_text="Number useful for classifying the different volumes of an edition, but not necessarily of historical value",
                null=True,
                verbose_name="Volume number",
            ),
        ),
        migrations.AlterField(
            model_name="witness",
            name="volume_title",
            field=models.CharField(
                blank=True,
                max_length=500,
                null=True,
                verbose_name="Title of the volume",
            ),
        ),
        migrations.AlterField(
            model_name="work",
            name="author",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="webapp.person",
                verbose_name="Author",
            ),
        ),
        migrations.AlterField(
            model_name="work",
            name="date_max",
            field=models.IntegerField(
                blank=True, null=True, verbose_name="Maximum date"
            ),
        ),
        migrations.AlterField(
            model_name="work",
            name="date_min",
            field=models.IntegerField(
                blank=True,
                help_text="Enter a year in numeric format. Example: '1401' to '1500' to indicate the 15<sup>th</sup> century.",
                null=True,
                verbose_name="Minimum date",
            ),
        ),
        migrations.AlterField(
            model_name="work",
            name="lang",
            field=models.ManyToManyField(
                blank=True, to="webapp.language", verbose_name="Language"
            ),
        ),
        migrations.AlterField(
            model_name="work",
            name="notes",
            field=models.TextField(
                blank=True, max_length=1000, null=True, verbose_name="Additional notes"
            ),
        ),
        migrations.AlterField(
            model_name="work",
            name="place",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="webapp.place",
                verbose_name="Creation place",
            ),
        ),
        migrations.AlterField(
            model_name="work",
            name="title",
            field=models.CharField(max_length=600, verbose_name="Title"),
        ),
    ]
