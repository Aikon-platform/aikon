from django.db import models

from app.webapp.models.place import Place
from app.webapp.models.person import Person

from app.webapp.models.utils.functions import get_fieldname


def get_name(fieldname, plural=False):
    fields = {
        "pub_place": {"en": "publication place", "fr": "lieu de publication"},
        "publisher": {"en": "publisher", "fr": "éditeur/libraire"},
        "no_publisher": {"en": "no publisher", "fr": "pas d'éditeur"},
        # "no_pub_place": {"en": "unknown publication place", "fr": "lieu de publication inconnu"},
        "name": {"en": "title", "fr": "titre"},
        "name_info": {
            "en": "name without historical value, useful to distinguish several editions sharing date and place of publication",
            "fr": "nom sans valeur historique, utile pour distinguer plusieurs éditions partageant date et lieu de publication",
        },
    }
    return get_fieldname(fieldname, fields, plural)


# TODO make it a Searchable Model
class Edition(models.Model):
    class Meta:
        verbose_name = get_name("Edition")
        verbose_name_plural = get_name("Edition", True)
        app_label = "webapp"

    def __str__(self, light=False):
        if light:
            return self.name
        publisher = self.publisher.name if self.publisher else get_name("no_publisher")
        pub_place = self.place.__str__() if self.place else get_name("no_pub_place")
        return f"{self.name}, {publisher} ({pub_place})"

    name = models.CharField(
        verbose_name=get_name("name"),
        max_length=500,
        help_text=get_name("name_info"),
    )
    place = models.ForeignKey(
        Place,
        verbose_name=get_name("pub_place"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    publisher = models.ForeignKey(
        Person,
        verbose_name=get_name("publisher"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
