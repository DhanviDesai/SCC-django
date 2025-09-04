from django.urls import path

from . import views

urlpatterns = [
    path('<uuid:tournament_id>/', views.GetLeaderboard.as_view(), name='get-leaderboard'),
    path('published/<uuid:tournament_id>/', views.GetPublishedLeaderboard.as_view(), name='get-published-leaderboard'),
    path('publish/<uuid:tournament_id>/', views.PublishLeaderboard.as_view(), name='publish-leaderboard'),
]