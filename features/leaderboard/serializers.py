from rest_framework import serializers
from .models import Leaderboard, CompanyLeaderboard

class LeaderboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leaderboard
        fields = '__all__'

class CompanyLeaderboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyLeaderboard
        fields = '__all__'
