from rest_framework import serializers
from .models import StepMetric, MetricConfig

class MetricConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetricConfig
        fields = "__all__"

class StepMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = StepMetric
        fields = "__all__"