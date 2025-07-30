from django.shortcuts import render
from rest_framework.views import APIView
from features.utils.response_wrapper import success_response, error_response
from rest_framework import status
from features.utils.authentication import FirebaseAuthentication

from features.users.models import User


from .models import Token
from .serializers import TokenSerializer, RegisterTokenSerializer, UpdateTokenSerializer



# Create your views here.
class RegisterToken(APIView):
    def post(self, request):
        serializer = RegisterTokenSerializer(data=request.data)
        if serializer.is_valid():
            fcm_token = serializer.validated_data['fcm_token']
            token = Token.objects.create(token=fcm_token)
            return success_response(data=TokenSerializer(token).data, message="Token registered", status=status.HTTP_201_CREATED)
        return error_response(message=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UpdateToken(APIView):
    authentication_classes = [FirebaseAuthentication]
    def put(self, request):
        serializer = UpdateTokenSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = User.objects.get(firebase_uid=serializer.validated_data['user_id'])
                token = Token.objects.get(token=serializer.validated_data['fcm_token'])
                token.user = user
                token.save()
                return success_response(data=TokenSerializer(token).data, message="Token updated", status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return error_response(message="User not found", status=status.HTTP_404_NOT_FOUND)
            except Token.DoesNotExist:
                return error_response(message="Token not found", status=status.HTTP_404_NOT_FOUND)
        return error_response(message=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

