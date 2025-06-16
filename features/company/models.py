from django.db import models
import json

# Create your models here.
class Company(models.Model):
    company_id = models.CharField(max_length=128)
    company_name = models.CharField(max_length=80)
    company_logo = models.CharField(max_length=256)

    def __str__(self):
        return json.dumps({
            "company_id": self.company_id,
            "company_name": self.company_name,
            "company_logo": self.company_logo
        })