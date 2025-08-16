from rest_framework import serializers

from . models import TournamentType, Tournament

class NestedTournamentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tournament
        fields = ['id', 'name', 'team_size']

class TournamentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TournamentType
        fields = ['id', 'name']

class TournamentSerializer(serializers.ModelSerializer):
    total_registrants = serializers.SerializerMethodField()
    class Meta:
        model = Tournament
        fields = ['id', 'name', 'sport', 'season', 'type', 'start_date', 'end_date', 'registration_start_date', 'registration_end_date',
                  'cities', 'description', 'total_registrants', 'created_at', 'updated_at', 'status', 'team_size']
    
    def get_total_registrants(self, obj):
        if obj.isIndividual():
            return obj.user.all().count()
        if obj.isTeam():
            return obj.tournament_team.filter(is_registered=True).count()
