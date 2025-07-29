from django.db import models

from features.users.models import User
from features.tournament.models import Tournament

# Create your models here.
class Team(models.Model):
    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=256)
    members = models.ManyToManyField(User, related_name='members')
    tournament = models.ManyToManyField(Tournament, related_name='tournament_team')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

class Invite(models.Model):
    id = models.UUIDField(primary_key=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True) # The user would be invited to this team
    invitee = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_invites", null=True) # This user would be invited
    inviter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_invites", null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()