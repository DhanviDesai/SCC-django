from django.urls import path

from . import views

urlpatterns = [
    path("firebase-login", views.FirebaseLogin.as_view(), name="firebase login"),
    path("admin-login", views.AdminLogin.as_view(), name="Admin login"),
    path("list", views.ListUsers.as_view(), name="list users"),
    path("filter", views.ListFilteredUsers.as_view(), name="List users in a company"),
    path("tournament", views.ListTournaments.as_view(), name="List tournaments the user has registered to"),
    path("", views.GetMe.as_view(), name="Get user details"),
]