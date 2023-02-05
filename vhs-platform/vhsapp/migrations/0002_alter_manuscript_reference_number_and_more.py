# Generated by Django 4.0.4 on 2023-02-03 17:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vhsapp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='manuscript',
            name='reference_number',
            field=models.CharField(max_length=150, verbose_name='Cote'),
        ),
        migrations.AlterField(
            model_name='manuscript',
            name='remarks',
            field=models.TextField(blank=True, verbose_name='Remarques'),
        ),
    ]
