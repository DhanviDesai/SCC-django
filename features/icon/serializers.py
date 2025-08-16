from rest_framework import serializers
from .models import Icon

class IconSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)
    name = serializers.CharField(required=False)

    class Meta:
        model = Icon
        fields = ('id', 'name', 'url', 'file')
        read_only_fields = ('url',)
