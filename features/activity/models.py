from django.db import models

from features.metric.models import MetricConfig
from features.users.models import User
from datetime import date

# Create your models here.
class ActivityConfig(models.Model):
    activity_type = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)
    metrics = models.ManyToManyField(MetricConfig, related_name="metrics")

class ActivityData(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activity_data")
    activity = models.ForeignKey(ActivityConfig, on_delete=models.CASCADE, related_name="activity_data")
    start_date = models.DateField(default=date.today)
    end_date = models.DateField(null=True, blank=True)

class ActivityMetric(models.Model):
    activity_data = models.ForeignKey(ActivityData, on_delete=models.SET_NULL, null=True, related_name="metrics")
    metric = models.ForeignKey(MetricConfig, on_delete=models.SET_NULL, null=True, related_name="activity_metrics")
    value = models.BigIntegerField()

    class Meta:
        unique_together = ('activity_data', 'metric')

