from rest_framework.serializers import ModelSerializer, Serializer, CharField, DateField
from .models import Season

class SeasonSerializer(ModelSerializer):
    class Meta:
        model = Season
        fields = ['id', 'name', 'start_date', 'end_date']

class SeasonCreateSerializer(Serializer):
    season_name = CharField(max_length=128)
    start_date = DateField(required=False)
    end_date = DateField(required=False)

    def create(self, validated_data):
        validated_data['name'] = validated_data.pop('season_name')
        return Season.objects.create(**validated_data)