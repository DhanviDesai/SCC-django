from django.urls import path

from . import views

urlpatterns = [
    path('<uuid:tournament_id>/', views.GetLeaderboard.as_view(), name='get_leaderboard'),
]