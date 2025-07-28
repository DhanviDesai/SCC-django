from django.db import models

from features.city.models import City
from features.sport.models import Sport
from features.season.models import Season

# Create your models here.
class TournamentType(models.Model):
    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=180)

class Tournament(models.Model):
    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=128)
    season = models.ForeignKey(Season, on_delete=models.CASCADE, default=None)
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, default=None, related_name="sports")
    type = models.ForeignKey(TournamentType, on_delete=models.CASCADE, default=None)
    description = models.TextField(null=True, blank=True, default=None)
    registration_start_date = models.DateField(null=True, blank=True)
    registration_end_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    cities = models.ManyToManyField(City, related_name='cities')
    schedule = models.CharField(max_length=256, null=True, default=None)

    def isIndividual(self, request):
        return self.type.name.lower().contains("individual")


