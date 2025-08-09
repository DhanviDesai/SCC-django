from django.urls import path

from . import views

urlpatterns = [
    path("create", views.CreateTeam.as_view(), name="create-team"),
    path("list", views.ListTeams.as_view(), name="list-my-teams"),
    path("list/all", views.ListAllTeams.as_view(), name="list-all-teams"),
    path("invite/received", views.ListReceivedInvites.as_view(), name="list-received-invites"),
    path("invite/sent", views.ListSentInvites.as_view(), name="list-sent-invites"),
    path("<slug:team_id>/invite", views.InviteUser.as_view(), name="invite-user-to-team"),
    path("invite/<slug:invite_id>/accept", views.AcceptInvite.as_view(), name='accept-invite'),
    path("invite/<slug:invite_id>/reject", views.RejectInvite.as_view(), name="reject-invite"),
    path("register/<slug:tournament_id>", views.RegisterTournament.as_view(), name="register-team-tournament"),
    path("<slug:id>", views.IndexOperations.as_view()),
]