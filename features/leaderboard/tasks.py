from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from datetime import timedelta
from features.strava.models import StravaActivity
from .models import Leaderboard, CompanyLeaderboard, LeaderboardSync

logger = get_task_logger(__name__)

@shared_task
def update_leaderboards():
    logger.info("Starting leaderboard update...")

    last_sync, _ = LeaderboardSync.objects.get_or_create(
        defaults={'last_processed_activity': timezone.now() - timedelta(days=30)}
    )

    new_activities = StravaActivity.objects.filter(created_at__gt=last_sync.last_processed_activity)

    for activity in new_activities:
        # Update user leaderboard
        leaderboard_entry, _ = Leaderboard.objects.get_or_create(
            user=activity.strava_user.user,
            tournament=activity.tournament
        )

        leaderboard_entry.total_distance += activity.details.get('distance', 0)
        leaderboard_entry.total_moving_time += activity.details.get('moving_time', 0)
        leaderboard_entry.total_elevation_gain += activity.details.get('total_elevation_gain', 0)
        leaderboard_entry.activity_count += 1
        leaderboard_entry.save()

        # Update company leaderboard
        if activity.strava_user.user.company:
            company_leaderboard_entry, _ = CompanyLeaderboard.objects.get_or_create(
                company=activity.strava_user.user.company,
                tournament=activity.tournament
            )

            company_leaderboard_entry.total_distance += activity.details.get('distance', 0)
            company_leaderboard_entry.total_moving_time += activity.details.get('moving_time', 0)
            company_leaderboard_entry.total_elevation_gain += activity.details.get('total_elevation_gain', 0)
            company_leaderboard_entry.activity_count += 1
            company_leaderboard_entry.save()

    last_sync.last_processed_activity = timezone.now()
    last_sync.save()

    logger.info("Leaderboard update finished.")
