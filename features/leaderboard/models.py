from django.db import models

from features.tournament.models import Tournament
from features.users.models import User
from features.team.models import Team

# Create your models here.
class Leaderboard(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    rank = models.BigIntegerField()

    class Meta:
        unique_together = ('tournament', 'user')

class TeamLeaderboard(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.SET_NULL, null=True)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True)
    rank = models.BigIntegerField()

    class Meta:
        unique_together = ('tournament', 'team')

class PublishedLeaderboard(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    rank = models.BigIntegerField()
    published_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('tournament', 'user')

class PublishedTeamLeaderboard(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.SET_NULL, null=True)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True)
    rank = models.BigIntegerField()
    published_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('tournament', 'team')

