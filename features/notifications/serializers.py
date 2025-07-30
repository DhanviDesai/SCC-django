from rest_framework import serializers
from .models import Token

class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = '__all__'

class RegisterTokenSerializer(serializers.Serializer):
    fcm_token = serializers.CharField()

class UpdateTokenSerializer(serializers.Serializer):
    fcm_token = serializers.CharField()
    user_id = serializers.CharField()