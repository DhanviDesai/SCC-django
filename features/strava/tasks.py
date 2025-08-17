import requests
from celery import shared_task
from django.utils import timezone
import time
from datetime import datetime, timedelta
from celery.utils.log import get_task_logger

from .models import StravaUser, StravaActivity, StravaSync
from .services import refresh_strava_token, get_club_activities
from features.tournament.models import Tournament

logger = get_task_logger(__name__)

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

@shared_task
def sync_strava_club_activities():
    logger.info("Starting Strava club activities sync...")
    tournaments = Tournament.objects.filter(strava_club_id__isnull=False)

    for tournament in tournaments:
        logger.info(f"Syncing activities for tournament: {tournament.name}")

        last_sync, _ = StravaSync.objects.get_or_create(
            tournament=tournament,
            defaults={'last_sync': timezone.now() - timedelta(days=30)} # Sync last 30 days for the first time
        )

        # We need a user's access token to fetch club activities.
        # We'll use the first user in the tournament. This assumes at least one user has connected their Strava account.

        strava_user = StravaUser.objects.filter(user__in=tournament.user.all()).first()

        if not strava_user:
            logger.warning(f"No Strava user found for tournament {tournament.name}. Skipping.")
            continue

        activities = get_club_activities(strava_user, tournament.strava_club_id, after=int(last_sync.last_sync.timestamp()))

        if activities is None:
            logger.error(f"Failed to fetch activities for tournament {tournament.name}. Skipping.")
            continue

        for activity_data in activities:
            strava_user_id = activity_data['athlete']['id']
            try:
                activity_strava_user = StravaUser.objects.get(strava_user_id=strava_user_id)

                # Check if activity already exists
                if StravaActivity.objects.filter(details__id=activity_data['id']).exists():
                    continue

                dt_object = datetime.fromisoformat(activity_data['start_date_local'].replace('Z', '+00:00'))
                date_object = dt_object.date()

                StravaActivity.objects.create(
                    strava_user=activity_strava_user,
                    tournament=tournament,
                    start_date=date_object,
                    sport_type=activity_data['type'],
                    details=activity_data
                )
            except StravaUser.DoesNotExist:
                logger.warning(f"No user found for Strava user ID: {strava_user_id}. Skipping activity.")
                continue

        last_sync.last_sync = timezone.now()
        last_sync.save()

    logger.info("Strava club activities sync finished.")
