import requests
from celery import shared_task
from django.utils import timezone
import time
from datetime import datetime

from .models import StravaUser, StravaActivity
from .services import refresh_strava_token
from features.tournament.models import Tournament, TournamentActivity, TournamentStatus
from features.users.models import User


@shared_task
def sync_strava_activities():
    # This task syncs activities for users in tournaments with a Strava club.
    # It iterates through each user and fetches their activities from the /athlete/activities endpoint.
    # The /clubs/{id}/activities endpoint is not used because it does not provide the athlete's ID,
    # making it impossible to link an activity to a user in our system.
    # Get all tournaments that have a club and are active
    tournaments = Tournament.objects.filter(
        club__isnull=False,
        status=TournamentStatus.ACTIVE,
        start_date__isnull=False,
        end_date__isnull=False
    )

    for tournament in tournaments:
        now = timezone.now()

        if tournament.last_synced_at:
            after_timestamp = int(tournament.last_synced_at.timestamp())
        else:
            after_timestamp = int(datetime.combine(tournament.start_date, datetime.min.time()).timestamp())

        # get users for the tournament
        for user in tournament.user.all():
            try:
                strava_user = StravaUser.objects.get(user=user)
            except StravaUser.DoesNotExist:
                continue # User has not connected their Strava account

            # Refresh token if necessary
            if strava_user.expires_at < int(time.time()):
                res = refresh_strava_token(strava_user)
                if not res:
                    # Log error and continue with next user
                    print(f"Failed to refresh token for user {user.email}. Aborting sync for this user.")
                    continue
                # reload user to get new token
                strava_user = StravaUser.objects.get(pk=strava_user.pk)

            headers = {'Authorization': f'Bearer {strava_user.access_token}'}

            before_timestamp = int(datetime.combine(tournament.end_date, datetime.max.time()).timestamp())

            activities_url = f"https://www.strava.com/api/v3/athlete/activities"
            params = {'before': before_timestamp, 'after': after_timestamp, 'per_page': 100}

            try:
                response = requests.get(activities_url, headers=headers, params=params)
                response.raise_for_status()
                activities = response.json()

                for activity_data in activities:
                    strava_activity_id = activity_data['id']

                    # Avoid duplicates for the same tournament
                    if TournamentActivity.objects.filter(strava_activity_id=strava_activity_id, tournament=tournament).exists():
                        continue

                    start_date = datetime.fromisoformat(activity_data['start_date'].replace('Z', '+00:00'))

                    TournamentActivity.objects.create(
                        tournament=tournament,
                        user=user,
                        strava_activity_id=strava_activity_id,
                        name=activity_data['name'],
                        distance=activity_data['distance'],
                        moving_time=activity_data['moving_time'],
                        elapsed_time=activity_data['elapsed_time'],
                        start_date=start_date,
                        sport_type=activity_data['sport_type']
                    )

            except requests.exceptions.RequestException as e:
                # Log the error and continue with the next user
                print(f"Error fetching activities for user {user.email}: {e}")
                continue

        # After processing all users for the tournament, update the last_synced_at timestamp
        tournament.last_synced_at = now
        tournament.save()

    return "Strava activities synced successfully."

@shared_task
def process_strava_event(event_data):
    owner_id = event_data.get('owner_id')
    object_id = event_data.get('object_id')
    aspect_type = event_data.get('aspect_type')

    if aspect_type != 'create' or not owner_id or not object_id:
        return "Not a create event or missing data. Skipping"
    
    if StravaActivity.objects.filter(strava_activity_id=object_id).exists():
        return f"Activity {object_id} already processed. Skipping."

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
        strava_activity = StravaActivity.objects.create(
            strava_activity_id=object_id,
            start_date=date_object, sport_type=activity_data['sport_type'],
                                                        details=activity_data)
        return f"Processed activity {object_id}"
    except requests.exceptions.RequestException as e:
        return f"Error fetching activity {object_id} from Strava: {e}"
