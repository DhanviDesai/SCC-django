from django.db import models

from features.users.models import User


# Create your models here.
class Token(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, default=True)
    token = models.CharField(max_length=256)
