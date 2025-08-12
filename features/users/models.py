from django.db import models
import json

from features.company.models import Company
# from features.tournament.models import Tournament

# Create your models here.
class GenderTypes(models.TextChoices):
    NA = "NA"
    Male = "Male"
    Female = "Female"
    Others = "Others"

class User(models.Model):
    firebase_uid = models.CharField(max_length=64, primary_key=True)
    username = models.CharField(max_length=128, blank=True, null=True)
    email = models.CharField(max_length=80)
    dob = models.DateField("date of birth", blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, blank=True, null=True)
    role = models.JSONField(default=list, help_text="List of roles assigned to the user")
    employee_code = models.CharField(max_length=56, null=True, blank=True)
    # tournament = models.ManyToManyField(Tournament, related_name='tournament_user')
    fcm_token = models.TextField(null=True)
    gender = models.CharField(max_length=20, choices=GenderTypes.choices, default=GenderTypes.NA)

    def __str__(self):
        return json.dumps({"user_id": self.firebase_uid, "email": self.email, "roles": str(self.role)})
