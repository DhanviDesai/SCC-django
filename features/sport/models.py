from django.db import models

from features.sport_type.models import SportType

# Create your models here.
class Sport(models.Model):
    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=128, unique=True)
    description = models.TextField()
    sport_type = models.ForeignKey(SportType, on_delete=models.CASCADE)
