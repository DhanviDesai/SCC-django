from django.db import models

from features.sport_type.models import SportType

# Create your models here.
class SportStatus(models.TextChoices):
    NA = "NA"
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"
    DRAFT = "DRAFT"

class Sport(models.Model):
    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=128, unique=True)
    description = models.TextField()
    sport_type = models.ForeignKey(SportType, on_delete=models.CASCADE)
    cover_image = models.CharField(max_length=256, null=True, blank=True)
    status = models.CharField(max_length=20, choices=SportStatus.choices, default=SportStatus.ACTIVE)
