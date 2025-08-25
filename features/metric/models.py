from django.db import models
from features.users.models import User

# Create your models here.
class MetricConfig(models.Model):
    metric_type = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)

class StepMetric(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    count = models.BigIntegerField()
