from django.urls import path

from . import views

urlpatterns = [
    path("list", views.ListSportType.as_view()),
    path("<uuid:type_id>", views.IndexOperations.as_view()),
]