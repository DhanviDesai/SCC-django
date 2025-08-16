from django.urls import path

from . import views

urlpatterns = [
    path("create", views.CreateTeam.as_view()),
    path("list", views.ListTeams.as_view()),
    path("list/all", views.ListAllTeams.as_view()),
    path("invite/received", views.ListReceivedInvites.as_view()),
    path("invite/sent", views.ListSentInvites.as_view()),
    path("invite/<uuid:team_id>", views.InviteUser.as_view()),
    path("invite/<uuid:invite_id>/accept", views.AcceptInvite.as_view(), name='accept-invite'),
    path("invite/<uuid:invite_id>/reject", views.RejectInvite.as_view()),
    path("register/<uuid:tournament_id>", views.RegisterTournament.as_view()),
    path("<uuid:id>", views.IndexOperations.as_view()),
]