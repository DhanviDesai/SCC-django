from django.urls import path

from . import views

urlpatterns = [
    path("list", views.ListTeams.as_view()),
    path("list/all", views.ListAllTeams.as_view()),
    path("<slug:id>", views.IndexOperations.as_view()),
]