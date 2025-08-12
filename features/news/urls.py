from django.urls import path
from . import views

urlpatterns = [
    path("list", views.ListNews.as_view(), name='list-news'),
    path("add", views.AddNews.as_view(), name='add-news'),
    path("carousel", views.ListCarousel.as_view(), name='list-carousel'),
    path("<slug:id>", views.IndexOperations.as_view(), name='index-operations'),
]