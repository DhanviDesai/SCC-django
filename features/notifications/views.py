from django.shortcuts import render
from rest_framework.views import APIView
from features.utils.response_wrapper import success_response, error_response
from rest_framework import status
from features.utils.authentication import FirebaseAuthentication

from features.users.models import User


from .models import Token
from .serializers import TokenSerializer



# Create your views here.
class RegisterToken(APIView):
    def post(self, request):
        fcm_token = request.data.get('fcm_token')
        if fcm_token is None:
            return error_response(message="FCM token is required", status=status.HTTP_400_BAD_REQUEST)
        token = Token.objects.create(token=fcm_token)
        return success_response(data=TokenSerializer(token).data, message="Token registered", status=status.HTTP_201_CREATED)

class UpdateToken(APIView):
    authentication_classes = [FirebaseAuthentication]
    def put(self, request):
        fcm_token = request.data.get('fcm_token')
        if fcm_token is None:
            return error_response(message="FCM token is required", status=status.HTTP_400_BAD_REQUEST)
        user_id = request.data.get('user_id')
        if user_id is None:
            return error_response(message="User id is required", status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.get(firebase_uid=user_id)
        token = Token.objects.get(token=fcm_token)
        token.user = user
        token.save()
        return success_response(data=TokenSerializer(token).data, message="Token updated", status=status.HTTP_200_OK)

