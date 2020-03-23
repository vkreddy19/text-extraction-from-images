from django.db import models


class Burials(models.Model):
    id = models.CharField(primary_key=True, max_length=50, blank=True, unique=True)
    name = models.CharField(max_length=50, blank=True)
    date = models.CharField(max_length=50, blank=True, null=True)
    section = models.CharField(max_length=50, blank=True)
    lot = models.CharField(max_length=50, blank=True)
    grave = models.CharField(max_length=50, blank=True)
    form_type = models.CharField(max_length=50, blank=True)
    time = models.DateTimeField(null=True)
    image_name = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.name


class Deeds(models.Model):
    # Business Info
    pass