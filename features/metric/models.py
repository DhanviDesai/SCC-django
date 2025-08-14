from django.db import models
from features.users.models import User

# Create your models here.

class StepMetric(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    count = models.BigIntegerField()
