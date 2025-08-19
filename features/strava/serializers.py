from rest_framework import serializers
from . models import StravaClub

class StravaSerializer(serializers.Serializer):
    exists = serializers.BooleanField()
    authorization_url = serializers.CharField(max_length=200, default=None)

class StravaClubSerializer(serializers.ModelSerializer):
    class Meta:
        model = StravaClub
        fields = '__all__'