import requests
from celery import shared_task
from django.utils import timezone
import time
from datetime import datetime

from .models import StravaUser, StravaActivity
from .services import refresh_strava_token

@shared_task
def process_strava_event(event_data):
    owner_id = event_data.get('owner_id')
    object_id = event_data.get('object_id')
    aspect_type = event_data.get('aspect_type')

    if aspect_type != 'create' or not owner_id or not object_id:
        return "Not a create event or missing data. Skipping"
    
    try:
        strava_user = StravaUser.objects.get(strava_user_id=owner_id)
    except StravaUser.DoesNotExist:
        return f"No user found for Strava owner_id: {owner_id}"
    
    if strava_user.expires_at < int(time.time()):
        res = refresh_strava_token(strava_user)
        if not res:
            return "Failed to refresh token. Aborting"
    
    activity_url = f"https://www.strava.com/api/v3/activities/{object_id}"
    headers = {'Authorization': f'Bearer {strava_user.access_token}'}

    try:
        response = requests.get(activity_url, headers=headers)
        response.raise_for_status()
        activity_data = response.json()
        dt_object = datetime.fromisoformat(activity_data['start_date_local'].replace('Z', '+00:00'))
        date_object = dt_object.date()
        strava_activity = StravaActivity.objects.create(start_date=date_object, sport_type=activity_data['sport_type'],
                                                        details=activity_data)
        return f"Processed activity {object_id}"
    except requests.exceptions.RequestException as e:
        return f"Error fetching activity {object_id} from Strava: {e}"
