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
from features.utils.permissions import HasRole

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
            username = request.data.get('username', '')
            dob = request.data.get('dob', '')
            company = request.data.get('company', '')
            user.username = username
            user.dob = dob
            user.company = Company.objects.get(company_id=company)
            user.save()
            return success_response(UserSerializer(user).data, message="User updated", status=status.HTTP_200_OK)
        except Exception as e:
            return error_response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class FirebaseLogin(APIView):
    def post(self, request):
        firebase_token = request.data.get('firebase_token')
        if not firebase_token:
            return error_response(message="Firebase token not provided", status=status.HTTP_400_BAD_REQUEST)
        decoded_token = auth.verify_id_token(firebase_token)
        uid = decoded_token['uid']
        email = decoded_token.get('email')
        user, created = User.objects.get_or_create(firebase_uid=uid)
        if created:
            user.email = email
            user.save()
        seriazlier = UserSerializer(user)
        return success_response(data=seriazlier.data, message="User created", status=status.HTTP_201_CREATED)


class ListUsers(APIView):
    authentication_classes = [FirebaseAuthentication]
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return success_response(data=serializer.data, message="User list fetched")


class SetRoleView(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAuthenticated, lambda request, view: HasRole('Admin').has_permission(request, view)]

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