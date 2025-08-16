from django.urls import path

from . import views

urlpatterns = [
    path("type", views.TournamentTypeIndexOperations.as_view()),
    path("add", views.AddTournament.as_view()),
    path("list", views.ListTournament.as_view()),
    path("schedule/add", views.AddSchedule.as_view()),
    path("schedule/presigned-url", views.GetSchedulePresignedUrl.as_view()),
    path("list/<uuid:id>", views.ListRegistrants.as_view()),
    path("register/<uuid:id>", views.RegisterTournament.as_view()),
    path("delete/<uuid:id>", views.DeleteTournament.as_view()),
    path("submit/<uuid:tournament_id>", views.HandleIncomingData.as_view()),
    path("<uuid:id>", views.IndexOperations.as_view()),
]