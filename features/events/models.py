from django.db import models

# Create your models here.
class EventType(models.Model):
    event_type_id = models.UUIDField(primary_key=True)
    event_type_name = models.CharField(max_length=128, unique=True)

class EventPlace(models.Model):
    event_place_id = models.UUIDField(primary_key=True)
    event_place_name = models.CharField(max_length=80, unique=True)

class Event(models.Model):
    event_id = models.UUIDField(primary_key=True)
    event_name = models.CharField(max_length=256, unique=True)
    event_type = models.ForeignKey(EventType, on_delete=models.CASCADE)
    event_venue = models.JSONField(default=list, blank=True, null=True)
    event_start_date = models.DateField(help_text="Start date of event")
    event_end_date = models.DateField(help_text="End date of event")
    event_registration_start_date = models.DateField(help_text="Users can register to events starting from this date")
    event_registration_end_date = models.DateField(help_text="Users have to register to events before this date")