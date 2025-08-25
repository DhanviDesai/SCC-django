from django.db import models

import uuid

from features.city.models import City
from features.sport.models import Sport
from features.season.models import Season
from features.users.models import User
from features.activity.models import ActivityConfig

# Create your models here.
class TournamentType(models.Model):
    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=180)

class TournamentStatus(models.TextChoices):
    NA = "NA"
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"
    DRAFT = "DRAFT"

class Tournament(models.Model):
    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=128)
    season = models.ForeignKey(Season, on_delete=models.CASCADE, default=None)
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, default=None, related_name="sports", db_index=True)
    type = models.ForeignKey(TournamentType, on_delete=models.CASCADE, default=None)
    description = models.TextField(null=True, blank=True, default=None)
    registration_start_date = models.DateField(null=True, blank=True)
    registration_end_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    cities = models.ManyToManyField(City, related_name='cities', db_index=True)
    schedule = models.CharField(max_length=256, null=True, default=None)
    user = models.ManyToManyField(User, related_name="tournament_user")
    team_size = models.IntegerField(default=None, null=True)
    created_at = models.DateTimeField(null=True, default=None)
    updated_at = models.DateTimeField(null=True, default=None)
    status = models.CharField(max_length=20, choices=TournamentStatus.choices, default=TournamentStatus.ACTIVE)
    activity = models.ForeignKey(ActivityConfig, on_delete=models.SET_NULL, null=True, default=None, related_name="tournament_activity", db_index=True)


    def isIndividual(self):
        return "individual" in self.type.name.lower()
    
    def isTeam(self):
        return "team" in self.type.name.lower()
    
    def isOnline(self):
        return "online" in self.type.name.lower()
    
    def isOnGround(self):
        return "ground" in self.type.name.lower()

class OnlineIndividualData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    data = models.IntegerField(default=-1)
    entry_date = models.DateField(db_index=True, null=True)


