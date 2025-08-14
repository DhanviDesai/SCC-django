from rest_framework import serializers

class StravaSerializer(serializers.Serializer):
    exists = serializers.BooleanField()
    authorization_url = serializers.CharField(max_length=200, default=None)