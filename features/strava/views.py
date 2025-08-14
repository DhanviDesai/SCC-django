from django.shortcuts import render
from django.urls import reverse
from rest_framework.views import APIView
import requests
from django.conf import settings
from urllib.parse import urlunparse, urlencode, ParseResult
from rest_framework import status
import json
from rest_framework.response import Response

from features.users.models import User
from features.utils.authentication import FirebaseAuthentication
from features.utils.response_wrapper import success_response, error_response

from .models import StravaUser
from .serializers import StravaSerializer
from .tasks import process_strava_event

# Create your views here.
class GetAuthorize(APIView):
    authentication_classes = [FirebaseAuthentication]
    
    def get(self, request):
        # Get the user
        uid = request.auth.get('user_id')
        user = User.objects.get(firebase_uid=uid)

        # Check if user is already authorized
        if StravaUser.objects.filter(user=user).exists():
            response = {
                'exists': True,
            }
            return success_response(data=StravaSerializer(response).data)
        
        # Construct the authorize URL
        # https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://yourdomain.com/exchange_token&approval_prompt=auto&scope=activity:read_all

        # Construct redirect uri
        redirect_uri = urlunparse(ParseResult('https', settings.HOST, reverse('strava-exchange-token'), params='', query=urlencode({
            'uid': uid,
        }), fragment=''))

        url_parts = ParseResult('https', settings.STRAVA_OAUTH_URL, path='', params='', query=urlencode({
            'client_id': settings.STRAVA_CLIENT_ID,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'approval_prompt': 'auto',
            'scope': 'activity:read_all'
        }), fragment='')
        response = {
            'exists': False,
            'authorization_url': urlunparse(url_parts)
        }
        return success_response(data=StravaSerializer(response).data, message="Successfully generated authorize url for the user")

class ExchangeToken(APIView):
    # No authentication needed as this is called by the OAUTH client
    def get(self, request):
        # Get the user
        uid = request.GET.get('uid')
        user = User.objects.get(firebase_uid=uid)

        # Get the code here
        code = request.GET.get('code')

        # Exchange the code for access token
        response = requests.post('https://www.strava.com/api/v3/oauth/token',
                                 data={
                                     'client_id': settings.STRAVA_CLIENT_ID,
                                     'client_secret': settings.STRAVA_CLIENT_SECRET,
                                     'code': code,
                                     'grant_type': 'authorization_code'
                                 })
        strava_access_token = response.json()['access_token']
        strava_refresh_token = response.json()['refresh_token']
        strava_token_expires_at = response.json()['expires_at']
        strava_athlete_id = response.json()['athlete']['id']
        strava_user = StravaUser.objects.create(user=user, strava_user_id=strava_athlete_id, 
                                                access_token=strava_access_token, refresh_token=strava_refresh_token, expires_at=strava_token_expires_at)

        # Redirect the user to a success page
        return render(request, 'strava/index.html')
        # return success_response(status=status.HTTP_201_CREATED)
        
class RefreshActivities(APIView):
    authentication_classes = [FirebaseAuthentication]

    def get(self, request):
        
        # Get the user
        uid = request.auth.get('user_id')
        user = User.objects.get(firebase_uid=uid)

        # Get the strava user
        strava_user = StravaUser.objects.get(user=user)
        print(strava_user.access_token)

        response = requests.get("https://www.strava.com/api/v3/athlete/activities", headers={
            'Authorization': f'Bearer {strava_user.access_token}'
        })
        print(response.status_code)
        print(response.json())

class StravaWebhookView(APIView):
    def get(self, request):
        challenge = request.GET.get('hub.challenge')
        verify_token = request.GET.get('hub.verify_token')

        print(challenge)

        if challenge:
            response_data = {'hub.challenge': challenge}
            return Response(response_data)
        return error_response()
    
    def post(self, request):
        print("Webhook event received:")
        print(json.dumps(request.data, indent=2))
        process_strava_event.delay(request.data)
        return success_response()

