from rest_framework import serializers
from .models import Company

class CompanySerializer(serializers.ModelSerializer):
    total_employees = serializers.SerializerMethodField()
    class Meta:
        model = Company
        fields = ['company_id', 'company_logo', 'company_name', 'total_employees']
    
    def get_total_employees(self, obj):
        return obj.user_set.count()