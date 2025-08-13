from django.db import models
import uuid

from features.users.models import User

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
    start_date = models.DateField()
    sport_type = models.CharField(max_length=20)
    details = models.JSONField()
