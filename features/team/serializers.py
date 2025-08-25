from . models import Team, Invite
from rest_framework.serializers import ModelSerializer

from features.tournament.serializers import NestedTournamentSerializer
from features.users.serializers import NestedUserSerializer

class NestedTeamSerializer(ModelSerializer):
    class Meta:
        model = Team
        fields =['id', 'name', 'is_registered']

class TeamSerializer(ModelSerializer):
    tournament = NestedTournamentSerializer(many=True, read_only=True)
    members = NestedUserSerializer(many=True, read_only=True)
    created_by = NestedUserSerializer(read_only=True)
    class Meta:
        model = Team
        fields = ['id', 'name', 'members', 'tournament', 'is_registered', 'created_by']

class InviteSerializer(ModelSerializer):
    team = NestedTeamSerializer(read_only=True)
    tournament = NestedTournamentSerializer(read_only=True)
    class Meta:
        model = Invite
        fields = ['id', 'team', 'invitee', 'inviter', 'created_at', 'status', 'tournament']