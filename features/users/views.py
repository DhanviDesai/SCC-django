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

from rest_framework.pagination import PageNumberPagination
from rest_framework import generics
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

from .models import User, Company
from .serializers import UserSerializer, UserUpdateSerializer, FirebaseLoginSerializer, SetRoleSerializer
from features.tournament.models import Tournament
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
            serializer = UserUpdateSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return success_response(UserSerializer(user).data, message="User updated", status=status.HTTP_200_OK)
            return error_response(message=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return error_response(message="User not found", status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return error_response(message=str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class FirebaseLogin(APIView):
    authentication_classes = [FirebaseTokenAuthentication]
    def post(self, request):
        serializer = FirebaseLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(message=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        uid = request.auth.get('user_id')
        email = request.auth.get('email')
        user, created = User.objects.get_or_create(firebase_uid=uid)

        # If user already exists, then just return saying yes
        if not created:
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
        print(company_id)
        if company_id is None:
            return error_response(message="Company id cannot be null")
        try:
            target_company = Company.objects.get(company_id=company_id)
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
        serializer = SetRoleSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(message=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        target_email = serializer.validated_data['email']
        role_to_set = serializer.validated_data['role']
        
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