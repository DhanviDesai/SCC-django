from django.db import models


# Create your models here.
class Season(models.Model):
    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=128)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateField(default=None)
    updated_at = models.DateField(default=None)
