from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.NewsViewSet, basename='news')

urlpatterns = [
    path("carousel", views.ListCarousel.as_view(), name='list-carousel'),
    path("", include(router.urls)),
]