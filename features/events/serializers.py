from rest_framework import serializers
from .models import EventType, Event, EventPlace

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['event_id', 'event_name', 'event_type', 'event_venue', 'event_start_date', 'event_end_date', 'event_registration_start_date', 'event_registration_end_date']

class EventTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventType
        fields = ['event_type_id', 'event_type_name']

class EventPlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventPlace
        fields = ['event_place_id', 'event_place_name']