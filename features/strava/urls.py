from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'clubs', views.ClubViewSet, basename='clubs')

urlpatterns = [
    path('authorize', views.GetAuthorize.as_view(), name='get-authorize-url'),
    path('exchange_token', views.ExchangeToken.as_view(), name='strava-exchange-token'),
    path('refresh', views.RefreshActivities.as_view(), name='strava-refresh-activities'),
    path('webhook', views.StravaWebhookView.as_view(), name='strava-webhook'),
    path('', include(router.urls))
]