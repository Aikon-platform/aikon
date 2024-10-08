# Generated by Django 5.0.6 on 2024-06-19 14:47

import app.webapp.models.content
import app.webapp.models.digitization
import app.webapp.utils.iiif.validation
import django.core.validators
import django.db.models.deletion
import functools
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("webapp", "0006_alter_regions_options_alter_regions_digitization"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="conservationplace",
            options={
                "verbose_name": "Lieu de conservation",
                "verbose_name_plural": "Lieu de conservations",
            },
        ),
        migrations.AlterModelOptions(
            name="content",
            options={"verbose_name": "Contenu", "verbose_name_plural": "Contenus"},
        ),
        migrations.AlterModelOptions(
            name="digitization",
            options={
                "verbose_name": "Numérisation",
                "verbose_name_plural": "Numérisations",
            },
        ),
        migrations.AlterModelOptions(
            name="digitizationsource",
            options={
                "verbose_name": "Source de la numérisation",
                "verbose_name_plural": "Source de la numérisations",
            },
        ),
        migrations.AlterModelOptions(
            name="edition",
            options={"verbose_name": "Édition", "verbose_name_plural": "Éditions"},
        ),
        migrations.AlterModelOptions(
            name="language",
            options={"verbose_name": "Langue", "verbose_name_plural": "Langues"},
        ),
        migrations.AlterModelOptions(
            name="person",
            options={
                "verbose_name": "Acteur historique",
                "verbose_name_plural": "Acteur historiques",
            },
        ),
        migrations.AlterModelOptions(
            name="place",
            options={"verbose_name": "Lieu", "verbose_name_plural": "Lieus"},
        ),
        migrations.AlterModelOptions(
            name="regionpair",
            options={
                "verbose_name": "Paire de régions",
                "verbose_name_plural": "Paire de régionss",
            },
        ),
        migrations.AlterModelOptions(
            name="regions",
            options={"verbose_name": "Régions", "verbose_name_plural": "Régions"},
        ),
        migrations.AlterModelOptions(
            name="role",
            options={"verbose_name": "Rôle", "verbose_name_plural": "Rôles"},
        ),
        migrations.AlterModelOptions(
            name="series",
            options={"verbose_name": "Série", "verbose_name_plural": "Séries"},
        ),
        migrations.AlterModelOptions(
            name="treatment",
            options={
                "verbose_name": "Traitement",
                "verbose_name_plural": "Traitements",
            },
        ),
        migrations.AlterModelOptions(
            name="witness",
            options={
                "ordering": ["-place"],
                "verbose_name": "Témoin",
                "verbose_name_plural": "Témoins",
            },
        ),
        migrations.AlterModelOptions(
            name="work",
            options={"verbose_name": "Œuvre", "verbose_name_plural": "Œuvres"},
        ),
        migrations.AlterField(
            model_name="conservationplace",
            name="city",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="webapp.place",
                verbose_name="Ville",
            ),
        ),
        migrations.AlterField(
            model_name="conservationplace",
            name="license",
            field=models.URLField(blank=True, null=True, verbose_name="Licence"),
        ),
        migrations.AlterField(
            model_name="conservationplace",
            name="name",
            field=models.CharField(max_length=200, verbose_name="Lieu de conservation"),
        ),
        migrations.AlterField(
            model_name="content",
            name="date_max",
            field=models.IntegerField(
                blank=True, null=True, verbose_name="Date maximale"
            ),
        ),
        migrations.AlterField(
            model_name="content",
            name="date_min",
            field=models.IntegerField(
                blank=True,
                help_text="Saisissez une année au format numérique. Exemple : '1401' à '1500' pour indiquer le 15<sup>ème</sup> siècle.",
                null=True,
                verbose_name="Date minimale",
            ),
        ),
        migrations.AlterField(
            model_name="content",
            name="lang",
            field=models.ManyToManyField(
                blank=True, to="webapp.language", verbose_name="Langue"
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
                verbose_name="Jusqu'à la page/folio",
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
                verbose_name="De la page/folio",
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
                verbose_name="Lieu de création",
            ),
        ),
        migrations.AlterField(
            model_name="content",
            name="whole_witness",
            field=models.BooleanField(
                default=False,
                help_text="Le témoin ne contient-t-il que ce œuvre ?",
                verbose_name="Intégralité du témoin",
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
                verbose_name="Témoin",
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
                verbose_name="Œuvre",
            ),
        ),
        migrations.AlterField(
            model_name="digitization",
            name="images",
            field=models.ImageField(
                blank=True,
                help_text="Envoyez des images jusqu'à 2 Go.",
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
                help_text="Les images numérisées sont-elles libres de droits ?",
                verbose_name="Libre d'utilisation",
            ),
        ),
        migrations.AlterField(
            model_name="digitization",
            name="manifest",
            field=models.URLField(
                blank=True,
                help_text="<div class='tooltip'>\n                        <i class='fa-solid fa-circle-info'></i>\n                        <span class='tooltiptext'>Un manifeste permet de décrire et de partager des numérisations avec leurs métadonnées selon la norme IIIF.</span>\n                    </div>\n                    E.g.: <a href='https://gallica.bnf.fr/iiif/ark:/12148/btv1b60004321/manifest.json' target='_blank'>\n                    https://gallica.bnf.fr/iiif/ark:/12148/btv1b60004321/manifest.json</a>",
                validators=[app.webapp.utils.iiif.validation.validate_manifest],
                verbose_name="manifest",
            ),
        ),
        migrations.AlterField(
            model_name="digitization",
            name="source",
            field=models.ForeignKey(
                blank=True,
                help_text="Exemple : Gallica.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="webapp.digitizationsource",
                verbose_name="Source de la numérisation",
            ),
        ),
        migrations.AlterField(
            model_name="edition",
            name="name",
            field=models.CharField(
                help_text="Nom sans valeur historique, utile pour distinguer plusieurs éditions partageant date et lieu de publication",
                max_length=500,
                verbose_name="Titre",
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
                verbose_name="Lieu de publication",
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
                verbose_name="Éditeur/libraire",
            ),
        ),
        migrations.AlterField(
            model_name="language",
            name="lang",
            field=models.CharField(max_length=200, unique=True, verbose_name="Langue"),
        ),
        migrations.AlterField(
            model_name="person",
            name="date_max",
            field=models.IntegerField(
                blank=True, null=True, verbose_name="Date maximale"
            ),
        ),
        migrations.AlterField(
            model_name="person",
            name="date_min",
            field=models.IntegerField(
                blank=True, null=True, verbose_name="Date minimale"
            ),
        ),
        migrations.AlterField(
            model_name="person",
            name="name",
            field=models.CharField(max_length=200, unique=True, verbose_name="Nom"),
        ),
        migrations.AlterField(
            model_name="place",
            name="country",
            field=models.CharField(blank=True, max_length=150, verbose_name="Pays"),
        ),
        migrations.AlterField(
            model_name="place",
            name="name",
            field=models.CharField(max_length=200, unique=True, verbose_name="Nom"),
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
                verbose_name="Numérisation",
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
                verbose_name="Contenu",
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
                verbose_name="Acteur historique",
            ),
        ),
        migrations.AlterField(
            model_name="role",
            name="role",
            field=models.CharField(
                blank=True,
                choices=[
                    ("pub", "éditeur/diffuseur"),
                    ("aut", "auteur"),
                    ("ill", "enlumineur"),
                    ("sel", "libraire"),
                    ("cop", "copiste"),
                    ("dra", "dessinateur"),
                    ("eng", "graveur"),
                    ("tra", "traducteur"),
                ],
                max_length=150,
                verbose_name="Rôle",
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
                verbose_name="Série",
            ),
        ),
        migrations.AlterField(
            model_name="series",
            name="date_max",
            field=models.IntegerField(
                blank=True, null=True, verbose_name="Date maximale"
            ),
        ),
        migrations.AlterField(
            model_name="series",
            name="date_min",
            field=models.IntegerField(
                blank=True,
                help_text="Saisissez une année au format numérique. Exemple : '1401' à '1500' pour indiquer le 15<sup>ème</sup> siècle.",
                null=True,
                verbose_name="Date minimale",
            ),
        ),
        migrations.AlterField(
            model_name="series",
            name="edition",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="webapp.edition",
                verbose_name="Édition",
            ),
        ),
        migrations.AlterField(
            model_name="series",
            name="is_public",
            field=models.BooleanField(
                default=False,
                help_text="Les informations seront accessibles aux autres utilisateurs de la base.",
                verbose_name="Rendre public",
            ),
        ),
        migrations.AlterField(
            model_name="series",
            name="notes",
            field=models.TextField(
                blank=True,
                max_length=600,
                verbose_name="Éléments descriptifs du contenu",
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
                verbose_name="Lieu de conservation",
            ),
        ),
        migrations.AlterField(
            model_name="series",
            name="work",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="webapp.work",
                verbose_name="Œuvre",
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
                verbose_name="Numérisation",
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
                verbose_name="Édition",
            ),
        ),
        migrations.AlterField(
            model_name="witness",
            name="id_nb",
            field=models.CharField(
                blank=True, max_length=150, null=True, verbose_name="Cote"
            ),
        ),
        migrations.AlterField(
            model_name="witness",
            name="is_public",
            field=models.BooleanField(
                default=False,
                help_text="<i class='fa-solid fa-triangle-exclamation' None></i> Les informations seront accessibles aux autres utilisateurs de la base.",
                verbose_name="Rendre public",
            ),
        ),
        migrations.AlterField(
            model_name="witness",
            name="link",
            field=models.URLField(
                blank=True, verbose_name="Lien externe (catalogue en ligne, etc.)"
            ),
        ),
        migrations.AlterField(
            model_name="witness",
            name="nb_pages",
            field=models.IntegerField(
                blank=True, null=True, verbose_name="Nombre de pages/folios"
            ),
        ),
        migrations.AlterField(
            model_name="witness",
            name="notes",
            field=models.TextField(
                blank=True, max_length=3000, verbose_name="Notes complémentaires"
            ),
        ),
        migrations.AlterField(
            model_name="witness",
            name="page_type",
            field=models.CharField(
                choices=[("pag", "Paginé"), ("fol", "Folioté"), ("oth", "Autre")],
                default=("pag", "Paginé"),
                max_length=150,
                verbose_name="Type de pagination",
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
                verbose_name="Lieu de conservation",
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
                verbose_name="Série",
            ),
        ),
        migrations.AlterField(
            model_name="witness",
            name="type",
            field=models.CharField(
                choices=[
                    ("ms", "Manuscrit"),
                    ("tpr", "Typographie"),
                    ("wpr", "Bois gravés"),
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
                help_text="Numéro utile pour classer les différents tomes d'une édition, mais qui n'a pas nécessairement de valeur historique",
                null=True,
                verbose_name="Numéro de volume",
            ),
        ),
        migrations.AlterField(
            model_name="witness",
            name="volume_title",
            field=models.CharField(
                blank=True, max_length=500, null=True, verbose_name="Titre du volume"
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
                verbose_name="Auteur",
            ),
        ),
        migrations.AlterField(
            model_name="work",
            name="date_max",
            field=models.IntegerField(
                blank=True, null=True, verbose_name="Date maximale"
            ),
        ),
        migrations.AlterField(
            model_name="work",
            name="date_min",
            field=models.IntegerField(
                blank=True,
                help_text="Saisissez une année au format numérique. Exemple : '1401' à '1500' pour indiquer le 15<sup>ème</sup> siècle.",
                null=True,
                verbose_name="Date minimale",
            ),
        ),
        migrations.AlterField(
            model_name="work",
            name="lang",
            field=models.ManyToManyField(
                blank=True, to="webapp.language", verbose_name="Langue"
            ),
        ),
        migrations.AlterField(
            model_name="work",
            name="notes",
            field=models.TextField(
                blank=True,
                max_length=1000,
                null=True,
                verbose_name="Notes complémentaires",
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
                verbose_name="Lieu de création",
            ),
        ),
        migrations.AlterField(
            model_name="work",
            name="title",
            field=models.CharField(max_length=600, verbose_name="Titre"),
        ),
    ]
