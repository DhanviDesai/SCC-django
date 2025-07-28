from . models import Team
from rest_framework.serializers import ModelSerializer

class TeamSerializer(ModelSerializer):
    class Meta:
        model = Team
        fields = ['id', 'name', 'members', 'tournament']