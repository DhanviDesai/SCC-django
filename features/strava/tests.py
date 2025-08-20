from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock
from datetime import datetime, date, timedelta
import time
import uuid

from features.tournament.models import Tournament, TournamentType, TournamentStatus, TournamentActivity
from features.strava.models import StravaUser, StravaClub
from features.users.models import User
from features.season.models import Season
from features.sport.models import Sport, SportType
from features.strava.tasks import sync_strava_activities

class SyncStravaActivitiesTest(TestCase):

    def setUp(self):
        self.user = User.objects.create(firebase_uid='test_user_1', email='test1@example.com', strava_athlete_id='12345')
        self.strava_user = StravaUser.objects.create(user=self.user, strava_user_id='12345', access_token='test_token', refresh_token='test_refresh', expires_at=int(time.time()) + 3600)

        self.season = Season.objects.create(id=uuid.uuid4(), name="Test Season", start_date=date.today(), end_date=date.today() + timedelta(days=30), created_at=date.today(), updated_at=date.today())

        self.sport_type = SportType.objects.create(id=uuid.uuid4(), name="Test Sport Type")
        self.sport = Sport.objects.create(id=uuid.uuid4(), name="Test Sport", description="A test sport", sport_type=self.sport_type)

        self.tournament_type = TournamentType.objects.create(id=uuid.uuid4(), name="Online Individual")
        self.strava_club = StravaClub.objects.create(club_id='1', club_name='Test Club', club_link='http://strava.com/clubs/1')

        self.tournament = Tournament.objects.create(
            id=uuid.uuid4(),
            name="Test Tournament",
            season=self.season,
            sport=self.sport,
            type=self.tournament_type,
            status=TournamentStatus.ACTIVE,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            club=self.strava_club,
            last_synced_at=None,
        )
        self.tournament.user.add(self.user)

    @patch('features.strava.tasks.refresh_strava_token')
    @patch('features.strava.tasks.requests.get')
    def test_sync_strava_activities_creates_activities(self, mock_requests_get, mock_refresh_token):
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {'id': 1, 'name': 'Test Activity', 'distance': 1000, 'moving_time': 300, 'elapsed_time': 360, 'start_date': '2025-01-01T12:00:00Z', 'sport_type': 'Run'}
        ]
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response

        sync_strava_activities()

        self.assertEqual(TournamentActivity.objects.count(), 1)
        activity = TournamentActivity.objects.first()
        self.assertEqual(activity.strava_activity_id, 1)
        self.assertEqual(activity.user, self.user)
        self.assertEqual(activity.tournament, self.tournament)
        mock_refresh_token.assert_not_called()

    @patch('features.strava.tasks.refresh_strava_token')
    @patch('features.strava.tasks.requests.get')
    def test_sync_strava_activities_no_duplicates(self, mock_requests_get, mock_refresh_token):
        TournamentActivity.objects.create(
            tournament=self.tournament, user=self.user, strava_activity_id=1,
            name='Test Activity', moving_time=300, elapsed_time=360, start_date=datetime.now(), sport_type='Run'
        )

        mock_response = MagicMock()
        mock_response.json.return_value = [
            {'id': 1, 'name': 'Test Activity', 'distance': 1000, 'moving_time': 300, 'elapsed_time': 360, 'start_date': '2025-01-01T12:00:00Z', 'sport_type': 'Run'}
        ]
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response

        sync_strava_activities()

        self.assertEqual(TournamentActivity.objects.count(), 1)

    @patch('features.strava.tasks.refresh_strava_token', return_value=True)
    @patch('features.strava.tasks.requests.get')
    def test_sync_strava_activities_token_refresh(self, mock_requests_get, mock_refresh_token):
        self.strava_user.expires_at = int(time.time()) - 1
        self.strava_user.save()

        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response

        sync_strava_activities()

        mock_refresh_token.assert_called_once_with(self.strava_user)

    def test_sync_strava_activities_no_tournaments(self):
        Tournament.objects.all().delete()
        sync_strava_activities()
        self.assertEqual(TournamentActivity.objects.count(), 0)

    @patch('features.strava.tasks.requests.get')
    def test_sync_strava_activities_user_not_in_strava(self, mock_requests_get):
        self.strava_user.delete()
        sync_strava_activities()
        mock_requests_get.assert_not_called()
        self.assertEqual(TournamentActivity.objects.count(), 0)

    @patch('features.strava.tasks.requests.get')
    def test_sync_strava_activities_uses_last_synced_at(self, mock_requests_get):
        last_synced_at = timezone.now() - timedelta(days=1)
        self.tournament.last_synced_at = last_synced_at
        self.tournament.save()

        sync_strava_activities()

        mock_requests_get.assert_called_once()
        args, kwargs = mock_requests_get.call_args
        self.assertEqual(kwargs['params']['after'], int(last_synced_at.timestamp()))

    @patch('features.strava.tasks.requests.get')
    def test_sync_strava_activities_uses_start_date_if_no_last_synced_at(self, mock_requests_get):
        sync_strava_activities()

        expected_after = int(datetime.combine(self.tournament.start_date, datetime.min.time()).timestamp())
        mock_requests_get.assert_called_once()
        args, kwargs = mock_requests_get.call_args
        self.assertEqual(kwargs['params']['after'], expected_after)

    @patch('features.strava.tasks.requests.get')
    def test_sync_strava_activities_updates_last_synced_at(self, mock_requests_get):
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_requests_get.return_value = mock_response

        sync_strava_activities()

        self.tournament.refresh_from_db()
        self.assertIsNotNone(self.tournament.last_synced_at)
        self.assertTrue(timezone.now() - self.tournament.last_synced_at < timedelta(seconds=10))
