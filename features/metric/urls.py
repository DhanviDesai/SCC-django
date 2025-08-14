from django.urls import path
from . import views

urlpatterns = [
    path('step', views.StepMetricView.as_view(), name='step-metric')
]