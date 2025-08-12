from django.db import models
import uuid

from features.season.models import Season

# Create your models here.
class News(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.TextField(blank=False, null=False)
    description = models.TextField(blank=False, null=False)
    image_url = models.TextField(null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_carousel = models.BooleanField()
    season = models.ForeignKey(Season, on_delete=models.CASCADE, null=True)
