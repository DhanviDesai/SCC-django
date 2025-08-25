from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'config', views.MetricConfigViewSet, basename='metric')

urlpatterns = [
    path('', include(router.urls)),
    path('step', views.StepMetricView.as_view(), name='step-metric'),
]