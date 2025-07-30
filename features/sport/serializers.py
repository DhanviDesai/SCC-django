from rest_framework.serializers import ModelSerializer
from . models import Sport, SportType

class SportTypeSerializer(ModelSerializer):
    class Meta:
        model = SportType
        fields = ['id', 'name']

class SportSerializer(ModelSerializer):
    class Meta:
        model = Sport
        fields = ['id', 'name', 'description', 'sport_type', 'cover_image']

class SportCreateSerializer(ModelSerializer):
    class Meta:
        model = Sport
        fields = ['name', 'description', 'sport_type', 'cover_image']