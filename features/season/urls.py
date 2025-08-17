from django.urls import path

from . import views

urlpatterns = [
    path("list", views.ListSeason.as_view(), name="Get and Post operations on season"),
    path("<uuid:season_id>", views.IndexOperations.as_view(), name="Put and Delete operations on season"),
]