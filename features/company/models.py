from django.db import models
import json
import uuid

# Create your models here.
class CompanyStatus(models.TextChoices):
    NA = "NA"
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"
    DRAFT = "DRAFT"

class Company(models.Model):
    company_id = models.CharField(max_length=128)
    company_name = models.CharField(max_length=80)
    company_logo = models.CharField(max_length=256)
    status = models.CharField(max_length=20, choices=CompanyStatus.choices, default=CompanyStatus.ACTIVE)

    def __str__(self):
        return json.dumps({
            "company_id": self.company_id,
            "company_name": self.company_name,
            "company_logo": self.company_logo
        })