from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LeaderboardViewSet, CompanyLeaderboardViewSet

router = DefaultRouter()
router.register(r'user', LeaderboardViewSet)
router.register(r'company', CompanyLeaderboardViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
