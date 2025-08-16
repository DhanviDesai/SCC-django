from rest_framework import serializers
from .models import News
from features.icon.models import Icon
from features.icon.serializers import IconSerializer

class NewsSerializer(serializers.ModelSerializer):
    icon = IconSerializer(read_only=True)
    icon_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = News
        fields = ('id', 'title', 'description', 'image_url', 'created_at', 'updated_at', 'is_carousel', 'season', 'icon', 'icon_id')

    def create(self, validated_data):
        icon_id = validated_data.pop('icon_id', None)
        if icon_id:
            try:
                validated_data['icon'] = Icon.objects.get(id=icon_id)
            except Icon.DoesNotExist:
                raise serializers.ValidationError("Icon not found.")
        return News.objects.create(**validated_data)