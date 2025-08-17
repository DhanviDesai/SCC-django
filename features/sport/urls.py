from django.urls import path

from . import views

urlpatterns = [
    path("list", views.SportListView.as_view(), name="Post and Get operations on sports"),
    path("add", views.AddSport.as_view()),
    path("presigned-url", views.GetPresignedUrl().as_view()),
    path("<uuid:sport_id>", views.IndexOperations.as_view(), name="Put and Delete operations on sports"),
]