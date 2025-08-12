from rest_framework import serializers
from .models import User, GenderTypes

class GenderTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GenderTypes
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['firebase_uid', 'username', 'email', 'dob', 'company', 'employee_code', 'gender_type']