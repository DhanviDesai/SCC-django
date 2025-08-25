from rest_framework import serializers

from features.metric.serializers import MetricConfigSerializer

from . models import ActivityConfig, ActivityData, ActivityMetric

class ActivityConfigReadSerializer(serializers.ModelSerializer):
    metrics = MetricConfigSerializer(many=True)
    class Meta:
        model = ActivityConfig
        fields = "__all__"

class ActivityConfigWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityConfig
        fields = "__all__"

class ActivityMetricSerializer(serializers.ModelSerializer):
    metric = MetricConfigSerializer()
    class Meta:
        model = ActivityMetric
        fields = "__all__"

class ActivityDataSerializer(serializers.ModelSerializer):
    metrics = serializers.SerializerMethodField()
    activity = ActivityConfigReadSerializer()
    class Meta:
        model = ActivityData
        fields = ['user', 'activity', 'start_datetime', 'end_datetime', 'metrics']
    
    def get_metrics(self, obj):
        activity_metrics = ActivityMetric.objects.filter(activity_data=obj)
        return ActivityMetricSerializer(activity_metrics, many=True).data