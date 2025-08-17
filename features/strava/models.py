from django.db import models
import uuid

from features.users.models import User
from features.tournament.models import Tournament

# Create your models here.
class StravaUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    strava_user_id = models.TextField(null=False, unique=True)
    access_token = models.TextField()
    refresh_token = models.TextField()
    expires_at = models.BigIntegerField()

class StravaActivity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    strava_user = models.ForeignKey(StravaUser, on_delete=models.CASCADE, null=True)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, null=True)
    start_date = models.DateField()
    sport_type = models.CharField(max_length=20)
    details = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

class StravaSync(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tournament = models.OneToOneField(Tournament, on_delete=models.CASCADE)
    last_sync = models.DateTimeField()
