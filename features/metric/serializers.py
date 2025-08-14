from rest_framework import serializers
from .models import StepMetric

class StepMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = StepMetric
        fields = "__all__"