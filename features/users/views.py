from django.shortcuts import render
from django.http import HttpResponse, HttpRequest
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from firebase_admin import auth
from rest_framework_simplejwt.tokens import RefreshToken
from uuid import uuid4
from rest_framework.permissions import IsAuthenticated

from features.utils.authentication import FirebaseAuthentication,FirebaseTokenAuthentication
from features.utils.permissions import IsAdminRole
from features.tournament.serializers import TournamentSerializer

from rest_framework.pagination import PageNumberPagination
from rest_framework import generics
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

from .models import User, GenderTypes
from .serializers import UserSerializer, GenderTypeSerializer
from features.tournament.models import Tournament
from features.utils.response_wrapper import success_response, error_response
from features.company.models import Company
from . import services

import logging
import re
import base64

logger = logging.getLogger(__name__)
url_pattern = re.compile(r'https?://\S+')

# Create your views here.
class GetMe(APIView):
    authentication_classes = [FirebaseAuthentication]
    def get(self, request, uid):
        uid = request.auth.get("user_id")
        user = User.objects.get(firebase_uid=uid)
        serializer = UserSerializer(user)
        return success_response(data=serializer.data, message="User details fetched")
    
    def put(self, request, uid):
        uid = request.auth.get("user_id")
        try:
            user = User.objects.get(firebase_uid=uid)
            if request.data.get('username') is not None:
                user.username = request.data.get('username')
            if request.data.get('dob') is not None:
                user.dob = request.data.get('dob')
            if request.data.get('company') is not None:
                user.company = Company.objects.get(id=request.data.get('company'))
            if request.data.get('employee_code') is not None:
                user.employee_code = request.data.get('employee_code')
            if request.data.get('fcm_token') is not None:
                user.fcm_token = request.data.get('fcm_token')
            if request.data.get('strava_profile') is not None:
                link = base64.b64decode(request.data.get('strava_profile'))
                link = link.decode('utf-8')
                link = link.replace('\n', ' ')
                # Get only the URL:
                logger.info(link)
                strava_profile = url_pattern.search(link)
                logger.info(strava_profile)
                if strava_profile is None:
                    return error_response(message="strava_profile does not contain a valid strava profile link")
                strava_profile_link = strava_profile.group(0)
                if 'athletes' in strava_profile_link:
                    athlete_id = strava_profile_link.strip('/').split('/')[-1]
                else:
                    athlete_id = services.get_strava_athlete_id(strava_profile_link)
                logger.info(f"Found strava athlete id is {athlete_id}")
                user.strava_athlete_id = athlete_id
            if request.data.get('gender') is not None:
                try:
                    gender = GenderTypes.objects.get(id=request.data.get('gender'))
                    user.gender_type = gender
                except GenderTypes.DoesNotExist:
                    logger.error("Gender does not exist")
            user.save()
            return success_response(UserSerializer(user).data, message="User updated", status=status.HTTP_200_OK)
        except Exception as e:
            return error_response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_serializer(self, *args, **kwargs):
        return UserSerializer(*args, **kwargs)
    
    def options(self, request, *args, **kwargs):
        """
        Manually generate the metadata for an OPTIONS request.
        """
        # The metadata_class determines what the response should look like
        meta = self.metadata_class()
        
        # We need to get the serializer and pass it to determine the actions
        serializer = self.get_serializer()
        data = meta.determine_metadata(request, self)
        
        # For a detail view, you'd typically want PUT/PATCH actions
        data['actions'] = {
            'PUT': meta.get_serializer_info(serializer)
        }
        
        return Response(data)



class FirebaseLogin(APIView):
    authentication_classes = [FirebaseTokenAuthentication]
    def post(self, request):
        firebase_token = request.data.get('firebase_token')
        if not firebase_token:
            return error_response(message="Firebase token not provided", status=status.HTTP_400_BAD_REQUEST)
        fcm_token = request.data.get('fcm_token')
        uid = request.auth.get('user_id')
        email = request.auth.get('email')
        user, created = User.objects.get_or_create(firebase_uid=uid)

        # If user already exists, then just return saying yes
        if not created:
            if not fcm_token:
                user.fcm_token = fcm_token
                user.save()
            return success_response(data=UserSerializer(user).data, status=status.HTTP_200_OK)
        
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
    permission_classes = [IsAdminRole]
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return success_response(data=serializer.data, message="User list fetched")

class UserPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100

class ListFilteredUsers(generics.ListAPIView):
    authentication_classes = [FirebaseAuthentication]

    serializer_class = UserSerializer
    pagination_class = UserPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['username']
    search_fields = ['^username']

    def get(self, request, *args, **kwargs):
        company_id = request.GET.get('company_id', None)
        if company_id is None:
            return error_response(message="Company id cannot be null")
        try:
            target_company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return error_response(message="Company not found", status=status.HTTP_404_NOT_FOUND)
        self.queryset = User.objects.filter(company=target_company)
        return super().get(self, request, *args, **kwargs)
        

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
        
class ListTournaments(APIView):
    authentication_classes = [FirebaseAuthentication]
    def get(self, request):
        user = User.objects.get(firebase_uid = request.auth.get("user_id"))
        # Get list of all the tournaments the user has registered to
        queryset = user.tournament_user.all()
        return success_response(data=TournamentSerializer(queryset, many=True).data, message="Tournaments fetched successfully")

class ListGenderTypes(APIView):
    def get(self, request):
        logger.info("Returning gender types")
        return success_response(data=GenderTypeSerializer(GenderTypes.objects.all(), many=True).data)
