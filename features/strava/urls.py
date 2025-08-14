from django.urls import path

from . import views

urlpatterns = [
    path('authorize', views.GetAuthorize.as_view(), name='get-authorize-url'),
    path('exchange_token', views.ExchangeToken.as_view(), name='strava-exchange-token'),
    path('refresh', views.RefreshActivities.as_view(), name='strava-refresh-activities'),
    path('webhook', views.StravaWebhookView.as_view(), name='strava-webhook'),
]