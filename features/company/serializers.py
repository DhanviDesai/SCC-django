from rest_framework import serializers
from .models import Company

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['company_id', 'company_logo', 'company_name']

class CompanyCreateSerializer(serializers.Serializer):
    company_name = serializers.CharField(max_length=80)
    company_logo_link = serializers.CharField(max_length=256)

    def create(self, validated_data):
        validated_data['company_logo'] = validated_data.pop('company_logo_link')
        return Company.objects.create(**validated_data)

class CompanyUpdateSerializer(serializers.Serializer):
    company_name = serializers.CharField(max_length=80, required=False)
    company_logo_link = serializers.CharField(max_length=256, required=False)

    def update(self, instance, validated_data):
        instance.company_name = validated_data.get('company_name', instance.company_name)
        if 'company_logo_link' in validated_data:
            instance.company_logo = validated_data.get('company_logo_link')
        instance.save()
        return instance