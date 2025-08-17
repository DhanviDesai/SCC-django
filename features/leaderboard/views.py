from rest_framework import viewsets
from .models import Leaderboard, CompanyLeaderboard
from .serializers import LeaderboardSerializer, CompanyLeaderboardSerializer

class LeaderboardViewSet(viewsets.ModelViewSet):
    queryset = Leaderboard.objects.all().order_by('-total_distance')
    serializer_class = LeaderboardSerializer

class CompanyLeaderboardViewSet(viewsets.ModelViewSet):
    queryset = CompanyLeaderboard.objects.all().order_by('-total_distance')
    serializer_class = CompanyLeaderboardSerializer
