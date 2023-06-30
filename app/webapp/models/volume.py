from django.db import models

from app.webapp.models.edition import Edition

from app.webapp.models.utils.functions import get_fieldname


def get_name(fieldname, plural=False):
    return get_fieldname(fieldname, {}, plural)


class Volume(models.Model):
    class Meta:
        verbose_name = get_name("Volume")
        verbose_name_plural = get_name("Volume", True)
        app_label = "webapp"

    def __str__(self):
        return self.title

    title = models.CharField(
        verbose_name=get_name("title"), max_length=150, unique=True
    )
    edition = models.ForeignKey(
        Edition,
        verbose_name=get_name("Edition"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )


# class Volume(models.Model):
#     printed = models.ForeignKey(
#         Printed, verbose_name="Imprimé", on_delete=models.CASCADE
#     )
#     digitized_version = models.ForeignKey(
#         DigitizedVersion,
#         verbose_name="Source de la version numérisée",
#         blank=True,
#         help_text=DIGITIZED_VERSION_VOL_INFO,
#         on_delete=models.SET_NULL,
#         null=True,
#     )
#     manifest_final = models.BooleanField(
#         verbose_name="Valider les annotations",
#         default=False,
#         help_text=MANIFEST_INFO,
#     )
#     title = models.CharField(verbose_name="Titre du volume", max_length=600)
#     slug = models.SlugField(max_length=600)
#     number_identifier = models.CharField(
#         verbose_name="Numéro ou élément d'identification du volume", max_length=150
#     )
#     place = models.CharField(verbose_name="Lieu", max_length=150, help_text=PLACE_INFO)
#     date = models.CharField(max_length=150)
#     publishers_booksellers = models.CharField(
#         verbose_name="Éditeurs/libraires", max_length=150
#     )
#     comment = models.TextField(verbose_name="Commentaire éventuel", blank=True)
#     other_copies = models.TextField(verbose_name="Autre(s) exemplaire(s)", blank=True)
#     created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
#     updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)
#
#     class Meta:
#         verbose_name = "Volume"
#         verbose_name_plural = "Volumes"
#         app_label = "webapp"
#
#     def __str__(self):
#         return self.title
#
#     def save(self, *args, **kwargs):
#         self.slug = slugify(self.title)
#         # Call the parent save method to save the model
#         super().save(*args, **kwargs)
#
#     def get_metadata(self):
#         metadata = {
#             "Author": self.printed.author.name if self.printed.author else "No author",
#             "Number or identifier of self": self.number_identifier,
#             "Place": self.place,
#             "Date": self.date,
#             "Publishers/booksellers": self.publishers_booksellers,
#             "Description of work": self.printed.description,
#         }
#         if descriptive_elements := self.printed.descriptive_elements:
#             metadata["Descriptive elements of the content"] = descriptive_elements
#         if illustrators := self.printed.illustrators:
#             metadata["Illustrator(s)"] = illustrators
#         if engravers := self.printed.engravers:
#             metadata["Engraver(s)"] = engravers
#         if digitized_version := self.digitized_version:
#             metadata["Source of the digitized version"] = digitized_version.source
#         if comment := self.comment:
#             metadata["Comment"] = comment
#         if other_copies := self.other_copies:
#             metadata["Other copy(ies)"] = other_copies
#         if manifest := self.manifestvolume_set.first():
#             metadata["Source manifest"] = str(manifest)
#
#         return metadata
