from rest_framework.serializers import ModelSerializer
from .models import Season

class SeasonSerializer(ModelSerializer):
    class Meta:
        model = Season
        fields = ['id', 'name', 'start_date', 'end_date']