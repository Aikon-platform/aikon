from django.db import migrations
from django.db.models import Q


def delete_propagations(apps, schema_editor):
    """
    delete propagations (RegionPair.similarity_type==3) where RegionPair.category is None
    """
    RegionPair = apps.get_model("webapp", "RegionPair")
    RegionPair.objects.filter(Q(similarity_type=3) & Q(category=None)).delete()
    return


class Migration(migrations.Migration):
    dependencies = [
        ("webapp", "0022_treatment_info"),
    ]
    operations = [migrations.RunPython(delete_propagations)]
