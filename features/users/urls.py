from django.urls import path

from . import views

urlpatterns = [
    path("firebase-login", views.FirebaseLogin.as_view(), name="firebase login"),
    path("list", views.ListUsers.as_view(), name="list users"),
    path("<str:uid>", views.GetMe.as_view(), name="Get user details"),
]