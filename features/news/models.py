from django.db import models
import uuid

from features.season.models import Season
from features.icon.models import Icon

# Create your models here.
class News(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.TextField(blank=False, null=False)
    description = models.TextField(blank=False, null=False)
    image_url = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_carousel = models.BooleanField()
    season = models.ForeignKey(Season, on_delete=models.CASCADE, null=True)
    icon = models.ForeignKey(Icon, on_delete=models.SET_NULL, null=True, blank=True)
