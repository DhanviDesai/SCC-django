from rest_framework.serializers import ModelSerializer
from . models import SportType

class SportTypeSerializer(ModelSerializer):
    class Meta:
        model = SportType
        fields = ['id', 'name']