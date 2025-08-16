import requests
from django.conf import settings
from .models import StravaUser
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

def refresh_strava_token(strava_user: StravaUser):
    logger.info(f"Refreshing token for user {strava_user.strava_user_id}...")

    token_url = 'https://www.strava.com/api/v3/oauth/token'

    payload = {
        'client_id': settings.STRAVA_CLIENT_ID,
        'client_secret': settings.STRAVA_CLIENT_SECRET,
        'grant_type': 'refresh_token',
        'refresh_token': strava_user.refresh_token # Use the saved refresh token
    }

    try:
        response = requests.post(token_url, data=payload)
        response.raise_for_status()
        new_token_data = response.json()

        strava_user.access_token = new_token_data['access_token']
        strava_user.refresh_token = new_token_data['refresh_token']
        strava_user.expires_at = new_token_data['expires_at']
        strava_user.save()
        logger.info("Token refreshed successfully")
        return strava_user
    except requests.exceptions.RequestException as e:
        logger.error(f"Error refreshing Strava token: {e}")
        # Handle the error, maybe by notifying the user to re-authenticate
        return None

def set_up_webhook():
    # Let's subscribe to updates via webhooks
    subscription_url = 'https://www.strava.com/api/v3/push_subscriptions'

    payload = {
        'client_id': settings.STRAVA_CLIENT_ID,
        'client_secret': settings.STRAVA_CLIENT_SECRET,
        'callback_url': f'https://{settings.HOST}/api/strava/webhook',
        'verify_token': 'a_secret_string_of_your_choice' # A secret token you create
    }

    try:
        response = requests.post(url=subscription_url, data=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error creating webhook subscription: {e}")
        logger.error(f"Response body: {e.response.text}")
        

