from rest_framework import serializers
from .models import Leaderboard, TeamLeaderboard

class LeaderboardSerializer(serializers.ModelSerializer):
    rank_holder = serializers.SerializerMethodField()
    class Meta:
        model = Leaderboard
        fields = ['id', 'tournament', 'rank_holder', 'rank']
    
    def get_rank_holder(self, obj):
        return obj.user.username if obj.user else None

class TeamLeaderboardSerializer(serializers.ModelSerializer):
    rank_holder = serializers.SerializerMethodField()
    class Meta:
        model = TeamLeaderboard
        fields = ['id', 'tournament', 'rank_holder', 'rank']
    
    def get_rank_holder(self, obj):
        return obj.team.name if obj.team else None