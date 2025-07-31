from django.urls import path

from . import views

urlpatterns = [
    path("type", views.TournamentTypeIndexOperations.as_view()),
    path("add", views.AddTournament.as_view()),
    path("list", views.ListTournament.as_view()),
    path("schedule/add", views.AddSchedule.as_view()),
    path("schedule/presigned-url", views.GetSchedulePresignedUrl.as_view()),
    path("list/<slug:id>", views.ListRegistrants.as_view()),
    path("register/<slug:id>", views.RegisterTournament.as_view()),
    path("delete/<slug:id>", views.DeleteTournament.as_view()),
    path("submit/<slug:tournament_id>", views.HandleIncomingData.as_view()),
    path("<slug:id>", views.IndexOperations.as_view()),
]