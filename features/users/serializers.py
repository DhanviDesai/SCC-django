from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['firebase_uid', 'username', 'email', 'dob', 'company', 'employee_code']

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'dob', 'company', 'employee_code', 'fcm_token']
        extra_kwargs = {
            'username': {'required': False},
            'dob': {'required': False},
            'company': {'required': False},
            'employee_code': {'required': False},
            'fcm_token': {'required': False}
        }

class FirebaseLoginSerializer(serializers.Serializer):
    firebase_token = serializers.CharField()

class SetRoleSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.CharField()