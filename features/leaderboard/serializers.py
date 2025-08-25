from rest_framework.serializers import ModelSerializer
from .models import Leaderboard

class LeaderboardSerializer(ModelSerializer):
    class Meta:
        model = Leaderboard
        fields = ['id', 'tournament', 'user', 'rank']