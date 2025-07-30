from . models import Team, Invite
from rest_framework import serializers

class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['id', 'name', 'members', 'tournament']

class InviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invite
        fields = ['id', 'team', 'invitee', 'inviter', 'created_at']

class CreateTeamSerializer(serializers.Serializer):
    team_name = serializers.CharField()
    tournament_id = serializers.UUIDField()

class InviteUserSerializer(serializers.Serializer):
    user_id = serializers.CharField()