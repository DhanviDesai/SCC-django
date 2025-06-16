from django.shortcuts import render
from rest_framework.views import APIView
from uuid import uuid4
from rest_framework import status

from .models import Event, EventType, EventPlace
from .serializers import EventSerializer, EventTypeSerializer, EventPlaceSerializer

from features.utils.response_wrapper import success_response
from features.utils.authentication import FirebaseAuthentication
from features.utils.permissions import IsAdminRole

# Create your views here.
class ListEvents(APIView):
    authentication_classes = [FirebaseAuthentication]
    def get(self, request):
        events = Event.objects.all()
        serializer = EventSerializer(events, many=True)
        return success_response(data=serializer.data, message="Event list fetched")

class ListEventTypes(APIView):
    authentication_classes = [FirebaseAuthentication]
    def get(self, request):
        event_types = EventType.objects.all()
        serializer = EventTypeSerializer(event_types, many=True)
        return success_response(data=serializer.data, message="Event type list fetched")

class ListEventPlaces(APIView):
    authentication_classes = [FirebaseAuthentication]
    def get(self, request):
        event_places = EventPlace.objects.all().order_by('event_place_name')
        serializer = EventPlaceSerializer(event_places, many=True)
        return success_response(data=serializer.data, message="Event place list fetched")

class AddEvent(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAdminRole]
    def post(self, request):
        event_name = request.data.get('event_name')
        event_start_date = request.data.get('event_start_date')
        event_end_date = request.data.get('event_end_date')
        event_type = request.data.get('event_type')
        event_venue = request.data.get('event_venue', None)
        registration_start_date = request.data.get('registration_start_date')
        registration_end_date = request.data.get('registration_end_date')
        event_type_ins = EventType.objects.get(event_type_id=event_type)
        event = Event.objects.create(event_id=uuid4(), event_name=event_name, event_start_date=event_start_date,
                                     event_end_date=event_end_date, event_type=event_type_ins, event_venue=event_venue,
                                     event_registration_start_date=registration_start_date, event_registration_end_date=registration_end_date)
        event.save()
        return success_response(EventSerializer(event).data, message="Event created", status=status.HTTP_201_CREATED)