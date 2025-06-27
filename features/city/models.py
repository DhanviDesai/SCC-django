from django.db import models

# Create your models here.
class City(models.Model):
    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=128)
    state = models.CharField(max_length=128)
