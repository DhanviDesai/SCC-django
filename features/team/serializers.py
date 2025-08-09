from . models import Team, Invite
from rest_framework.serializers import ModelSerializer

class TeamSerializer(ModelSerializer):
    class Meta:
        model = Team
        fields = ['id', 'name', 'members', 'tournament', 'is_registered']

class InviteSerializer(ModelSerializer):
    class Meta:
        model = Invite
        fields = ['id', 'team', 'invitee', 'inviter', 'created_at']