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
