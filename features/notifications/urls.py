from django.urls import path
from . import views

urlpatterns = [
    path('register', views.RegisterToken.as_view()),
    path('update', views.UpdateToken.as_view()),
]