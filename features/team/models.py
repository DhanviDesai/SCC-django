from django.db import models

from features.users.models import User
from features.tournament.models import Tournament

# Create your models here.
class Team(models.Model):
    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=256)
    members = models.ManyToManyField(User, related_name='members')
    tournament = models.ManyToManyField(Tournament, related_name='tournament_team')
