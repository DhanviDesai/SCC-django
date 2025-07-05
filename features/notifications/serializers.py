from rest_framework.serializers import ModelSerializer
from .models import Token

class TokenSerializer(ModelSerializer):
    class Meta:
        model = Token
        fields = '__all__'