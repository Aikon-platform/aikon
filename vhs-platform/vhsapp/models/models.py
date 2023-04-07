from django.db import models


class Author(models.Model):
    name = models.CharField(verbose_name="Nom", max_length=200, unique=True)

    class Meta:
        verbose_name = "Auteur"
        verbose_name_plural = "Auteurs"

    def __str__(self):
        return self.name


class Work(models.Model):
    title = models.CharField(verbose_name="Titre", max_length=600, unique=True)

    class Meta:
        verbose_name = "Titre"
        verbose_name_plural = "Titre"

    def __str__(self):
        return self.title


class DigitizedVersion(models.Model):
    source = models.CharField(max_length=150, unique=True)

    class Meta:
        verbose_name = "Source de la version numérisée"
        verbose_name_plural = "Sources des versions numérisées"

    def __str__(self):
        return self.source


class Place(models.Model):
    name = models.CharField(verbose_name="Nom", max_length=200, unique=True)
    country = models.CharField(verbose_name="Pays", max_length=150)
    latitude = models.DecimalField(
        verbose_name="Latitude", max_digits=8, decimal_places=4, null=True
    )
    longitude = models.DecimalField(
        verbose_name="Longitude", max_digits=8, decimal_places=4, null=True
    )

    class Meta:
        verbose_name = "Lieu"
        verbose_name_plural = "Lieux"

    def __str__(self):
        return self.name


class ConservationPlace(models.Model):
    name = models.CharField(
        verbose_name="Nom de l'établissement", max_length=200, unique=True
    )
    place_id = models.ForeignKey(
        Place, verbose_name="Ville", blank=True, on_delete=models.SET_NULL, null=True
    )

    class Meta:
        verbose_name = "Lieu de conservation"
        verbose_name_plural = "Lieux de conservation"

    def __str__(self):
        return self.name
