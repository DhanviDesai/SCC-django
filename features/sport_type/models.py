from django.db import models

# Create your models here.
class SportType(models.Model):
    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=80)