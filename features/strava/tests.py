from django.test import TestCase
from unittest.mock import patch, MagicMock
from .tasks import sync_strava_club_activities
from features.tournament.models import Tournament, TournamentType
from features.users.models import User
from features.strava.models import StravaUser, StravaSync, StravaActivity
from features.season.models import Season
from features.sport.models import Sport, SportType
import uuid
from django.utils import timezone

import datetime

class StravaTasksTestCase(TestCase):
    def setUp(self):
        self.season = Season.objects.create(
            id=uuid.uuid4(),
            name="Test Season",
            start_date=datetime.date(2025, 1, 1),
            end_date=datetime.date(2025, 12, 31),
            created_at=datetime.date.today(),
            updated_at=datetime.date.today()
        )
        self.sport_type = SportType.objects.create(id=uuid.uuid4(), name="Test Sport Type")
        self.sport = Sport.objects.create(id=uuid.uuid4(), name="Test Sport", sport_type=self.sport_type)
        self.tournament_type = TournamentType.objects.create(id=uuid.uuid4(), name="Online Individual")
        self.user = User.objects.create(firebase_uid="test_user_uid", email="test@example.com")
        self.strava_user = StravaUser.objects.create(
            user=self.user,
            strava_user_id="test_strava_user_id",
            access_token="test_access_token",
            refresh_token="test_refresh_token",
            expires_at=timezone.now().timestamp() + 3600
        )
        self.tournament = Tournament.objects.create(
            id=uuid.uuid4(),
            name="Test Tournament",
            season=self.season,
            sport=self.sport,
            type=self.tournament_type,
            strava_club_id=12345
        )
        self.tournament.user.add(self.user)

    @patch('features.strava.tasks.get_club_activities')
    def test_sync_strava_club_activities(self, mock_get_club_activities):
        mock_get_club_activities.return_value = [
            {
                'athlete': {'id': "test_strava_user_id"},
                'id': 'test_activity_id',
                'start_date_local': '2025-08-17T10:00:00Z',
                'type': 'Run',
                'distance': 1000,
                'moving_time': 300,
                'total_elevation_gain': 100
            }
        ]

        sync_strava_club_activities()

        mock_get_club_activities.assert_called_once()
        self.assertEqual(StravaSync.objects.count(), 1)
        self.assertEqual(StravaActivity.objects.count(), 1)
