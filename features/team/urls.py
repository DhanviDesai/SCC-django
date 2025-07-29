from django.urls import path

from . import views

urlpatterns = [
    path("create", views.CreateTeam.as_view()),
    path("list", views.ListTeams.as_view()),
    path("list/all", views.ListAllTeams.as_view()),
    path("invite/received", views.ListReceivedInvites.as_view()),
    path("invite/sent", views.ListSentInvites.as_view()),
    path("invite/<slug:id>", views.InviteUser.as_view()),
    path("<slug:id>", views.IndexOperations.as_view()),
]