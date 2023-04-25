from django.db import models


class Author(models.Model):
    name = models.CharField(verbose_name="Nom", max_length=200, unique=True)
    date_min = models.IntegerField(verbose_name="Date min", null=True, blank=True)
    date_max = models.IntegerField(verbose_name="Date max", null=True, blank=True)

    class Meta:
        verbose_name = "Auteur"
        verbose_name_plural = "Auteurs"

    def __str__(self):
        return self.name


class DigitizedVersion(models.Model):
    source = models.CharField(max_length=150, unique=True)

    class Meta:
        verbose_name = "Source de la version numérisée"
        verbose_name_plural = "Sources des versions numérisées"

    def __str__(self):
        return self.source
