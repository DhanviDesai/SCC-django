from django.db import models

from features.tournament.models import Tournament
from features.users.models import User

# Create your models here.
class Leaderboard(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    rank = models.BigIntegerField()

    class Meta:
        unique_together = ('tournament', 'user')
