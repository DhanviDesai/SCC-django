from django.db import models
import uuid

from features.users.models import User
from features.tournament.models import Tournament
from features.company.models import Company

class Leaderboard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    total_distance = models.FloatField(default=0)
    total_moving_time = models.FloatField(default=0)
    total_elevation_gain = models.FloatField(default=0)
    activity_count = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'tournament')

class CompanyLeaderboard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    total_distance = models.FloatField(default=0)
    total_moving_time = models.FloatField(default=0)
    total_elevation_gain = models.FloatField(default=0)
    activity_count = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('company', 'tournament')

class LeaderboardSync(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    last_processed_activity = models.DateTimeField(null=True)
