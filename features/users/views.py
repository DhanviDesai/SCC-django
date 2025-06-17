from django.shortcuts import render
from django.http import HttpResponse, HttpRequest
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from firebase_admin import auth
from rest_framework_simplejwt.tokens import RefreshToken
from uuid import uuid4
from rest_framework.permissions import IsAuthenticated

from features.utils.authentication import FirebaseAuthentication
from features.utils.permissions import IsAdminRole

from .models import User, Company
from .serializers import UserSerializer
from features.utils.response_wrapper import success_response, error_response

# Create your views here.
class GetMe(APIView):
    authentication_classes = [FirebaseAuthentication]
    def get(self, request, uid):
        user = User.objects.get(firebase_uid=uid)
        serializer = UserSerializer(user)
        return success_response(data=serializer.data, message="User details fetched")
    
    def put(self, request, uid):
        try:
            user = User.objects.get(firebase_uid=uid)
            if request.data.get('username') is not None:
                user.username = request.data.get('username')
            if request.data.get('dob') is not None:
                user.dob = request.data.get('dob')
            if request.data.get('company') is not None:
                user.company = Company.objects.get(request.data.get('company'))
            if request.data.get('employee_code') is not None:
                user.employee_code = request.data.get('employee_code')
            user.save()
            return success_response(UserSerializer(user).data, message="User updated", status=status.HTTP_200_OK)
        except Exception as e:
            return error_response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class FirebaseLogin(APIView):
    authentication_classes = [FirebaseAuthentication]
    def post(self, request):
        firebase_token = request.data.get('firebase_token')
        if not firebase_token:
            return error_response(message="Firebase token not provided", status=status.HTTP_400_BAD_REQUEST)
        uid = request.auth.get('user_id')
        email = request.auth.get('email')
        user, created = User.objects.get_or_create(firebase_uid=uid)
        if created:
            user.email = email
            user.role = ['USER']
            user.save()
        firebase_user = auth.get_user(uid)
        current_claims = firebase_user.custom_claims if firebase_user.custom_claims else {}
        new_claims = {
            **current_claims,
            'roles': user.role
        }
        auth.set_custom_user_claims(uid, new_claims)
        seriazlier = UserSerializer(user)
        return success_response(data=seriazlier.data, message="User created", status=status.HTTP_201_CREATED)


class ListUsers(APIView):
    authentication_classes = [FirebaseAuthentication]
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return success_response(data=serializer.data, message="User list fetched")

class AdminLogin(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAdminRole]
    def get(self, request):
        firebase_user = auth.get_user(request.auth.get('user_id'))
        current_claims = firebase_user.custom_claims if firebase_user.custom_claims else {}
        if 'roles' not in current_claims:
            current_claims['roles'] = ['ADMIN']
        auth.set_custom_user_claims(request.auth.get('user_id'), current_claims)
        return success_response()

class SetRoleView(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAdminRole]

    def post(self, request):
        target_email = request.data.get('email')
        role_to_set = request.data.get('role')

        if not target_email or not role_to_set:
            return Response(
                {
                    'error': 'Email and role are required'
                },
                status=status.HTTP_200_OK
            )
        
        try:
            user = auth.get_user_by_email(target_email)

            existing_claims = user.custom_claims or {}
            existing_roles = existing_claims.get('roles', [])

            if role_to_set not in existing_roles:
                existing_roles.append(role_to_set)
            
            auth.set_custom_user_claims(user.uid, {'roles': existing_roles})

            return Response(
                {
                    'message': f"Role '{role_to_set}' successfully added to {target_email}"
                },
                status=status.HTTP_200_OK
            )
        except auth.UserNotFoundError:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)