from rest_framework.serializers import ModelSerializer

from . models import TournamentType, Tournament

class TournamentTypeSerializer(ModelSerializer):
    class Meta:
        model = TournamentType
        fields = ['id', 'name']

class TournamentSerializer(ModelSerializer):
    class Meta:
        model = Tournament
        fields = ['id', 'name', 'sport', 'season', 'type', 'start_date', 'end_date', 'registration_start_date', 'registration_end_date',
                  'cities', 'description']