from rest_framework.serializers import ModelSerializer
from .models import Icon

class IconSerializer(ModelSerializer):
    class Meta:
        model = Icon
        fields = '__all__'
