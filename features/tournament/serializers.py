from rest_framework import serializers
from .models import TournamentType, Tournament
from features.city.models import City

class TournamentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TournamentType
        fields = ['id', 'name']

class TournamentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tournament
        fields = ['id', 'name', 'sport', 'season', 'type', 'start_date', 'end_date', 'registration_start_date', 'registration_end_date', 'cities', 'description']

class TournamentCreateSerializer(serializers.ModelSerializer):
    cities = serializers.PrimaryKeyRelatedField(queryset=City.objects.all(), many=True)

    class Meta:
        model = Tournament
        fields = ['name', 'sport', 'season', 'type', 'start_date', 'end_date', 'registration_start_date', 'registration_end_date', 'cities', 'description']

    def create(self, validated_data):
        cities = validated_data.pop('cities')
        tournament = Tournament.objects.create(**validated_data)
        tournament.cities.set(cities)
        return tournament

class AddScheduleSerializer(serializers.Serializer):
    file_url = serializers.CharField()
    tournament_id = serializers.UUIDField()