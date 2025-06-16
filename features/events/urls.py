from django.urls import path

from . import views

urlpatterns = [
    path("list", views.ListEvents.as_view(), name="List all events"),
    path("type/list", views.ListEventTypes.as_view(), name="List all event types"),
    path("place/list", views.ListEventPlaces.as_view(), name="List all event places"),
    path("add", views.AddEvent.as_view(), name="Add a new event"),
]