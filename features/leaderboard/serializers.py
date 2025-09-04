from rest_framework import serializers
from .models import Leaderboard, TeamLeaderboard

class DynamicLeaderboardSerializer(serializers.ModelSerializer):
    rank_holder = serializers.SerializerMethodField()
    points = serializers.SerializerMethodField()
    class Meta:
        model = Leaderboard
        fields = ['id', 'tournament', 'rank_holder', 'rank', 'points']
    
    def get_rank_holder(self, obj):
        return obj['user'].username if obj.get('user') else None
    
    def get_points(self, obj):
        return obj.get('total_score', 0)

class DynamicTeamLeaderboardSerializer(serializers.ModelSerializer):
    rank_holder = serializers.SerializerMethodField()
    points = serializers.SerializerMethodField()
    class Meta:
        model = TeamLeaderboard
        fields = ['id', 'tournament', 'rank_holder', 'rank', 'points']
    
    def get_rank_holder(self, obj):
        return obj['team'].name if obj.get('team') else None
    
    def get_points(self, obj):
        return obj.get('total_score', 0)

class PublishedLeaderboardSerializer(serializers.ModelSerializer):
    rank_holder = serializers.SerializerMethodField()
    class Meta:
        model = Leaderboard
        fields = ['id', 'tournament', 'rank_holder', 'rank', 'total_score', 'start_date', 'end_date']
    
    def get_rank_holder(self, obj):
        return obj.user.username if obj.user else None

class PublishedTeamLeaderboardSerializer(serializers.ModelSerializer):
    rank_holder = serializers.SerializerMethodField()
    class Meta:
        model = Leaderboard
        fields = ['id', 'tournament', 'rank_holder', 'rank', 'total_score', 'start_date', 'end_date']
    
    def get_rank_holder(self, obj):
        return obj.team.name if obj.team else None