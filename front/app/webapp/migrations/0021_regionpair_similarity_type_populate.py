# Generated by Django 5.1.6 on 2025-03-31 12:22

from django.db import migrations


def populate_similarity_type(apps, schema_editor):
    r"""
    possible values for similarity_type:
    1 = automated/computed similarity
    2 = manual similarity
    3 = propagated similarity (does not yet exist in database)

    /!\ should be used before any propagated matches are saved to database
    """
    RegionPair = apps.get_model("webapp", "RegionPair")
    RegionPair.objects.filter(is_manual=False).update(similarity_type=1)
    RegionPair.objects.filter(is_manual=True).update(similarity_type=2)
    return


class Migration(migrations.Migration):
    dependencies = [
        ("webapp", "0020_regionpair_similarity_type"),
    ]
    operations = [migrations.RunPython(populate_similarity_type)]
