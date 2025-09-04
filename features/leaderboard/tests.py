from django.test import TestCase
from rest_framework.test import APITestCase
import uuid
from django.urls import reverse
import logging

from features.users.models import User
from features.sport.models import SportType, Sport
from features.tournament.models import TournamentType, Tournament
from features.season.models import Season
from features.metric.models import MetricConfig
from features.activity.models import ActivityConfig, ActivityData, ActivityMetric
from features.team.models import Team
from datetime import timezone
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Create your tests here.
class LeaderboardTest(APITestCase):
    def setUp(self):
        # Create users
        self.user1 = User.objects.create(firebase_uid="123", username="123")
        self.user2 = User.objects.create(firebase_uid="abc", username="abc")
        self.user3 = User.objects.create(firebase_uid="ghi", username="ghi")
        self.user4 = User.objects.create(firebase_uid="xyz", username="xyz")
        self.user5 = User.objects.create(firebase_uid="lmn", username="lmn")
        self.user6 = User.objects.create(firebase_uid="opq", username="opq")

        # Create tournament that requires a team of 3
        now = datetime.now(tz=timezone.utc)
        
        # Create a season
        self.season = Season.objects.create(id=uuid.uuid4(), name="season1", created_at=now, updated_at=now)

        # Create a sport type
        self.sport_type = SportType.objects.create(id=uuid.uuid4(), name="1")

        # Create a sport
        self.sport = Sport.objects.create(id=uuid.uuid4(), name="sport1", description="a;djfa", sport_type=self.sport_type)

        # Insert MetricConfig
        self.metric_config = MetricConfig.objects.create(
            metric_type="Test Metric",
            description="Test Description"
        )

        self.metric_config_2 = MetricConfig.objects.create(
            metric_type="Test Metric 2",
            description="Test Description 2"
        )

        # Insert Activity
        self.activity = ActivityConfig.objects.create(
            activity_type="Test Activity",
            description="Test Activity Description",
        )
        self.activity.metrics.add(self.metric_config)

        # Create a tournament type
        self.tournament_type_team = TournamentType.objects.create(id=uuid.uuid4(), name="Online Team")
        self.tournament_type_individual = TournamentType.objects.create(id=uuid.uuid4(), name="Online Individual")

        # Create a tournament of team type
        self.team_tournament = Tournament.objects.create(
            id=uuid.uuid4(),
            name="tournament1",
            team_size=3,
            season=self.season,
            sport=self.sport,
            type=self.tournament_type_team,
            activity=self.activity
        )

        # Create a tournament of individual type
        self.individual_tournament = Tournament.objects.create(
            id=uuid.uuid4(),
            name="tournament2",
            season=self.season,
            sport=self.sport,
            type=self.tournament_type_individual,
            activity=self.activity
        )

        # Create a team with user1 and user2
        team = Team.objects.create(id=uuid.uuid4(), name="Test Team", created_by=self.user1)
        team.tournament.add(self.team_tournament)
        team.members.add(self.user1)
        team.members.add(self.user2)
        team.is_registered = True
        team.save()
        self.team = team

        # Create a team with user4 and user5
        team2 = Team.objects.create(id=uuid.uuid4(), name="Test Team 2", created_by=self.user4)
        team2.tournament.add(self.team_tournament)
        team2.members.add(self.user4)
        team2.members.add(self.user5)
        team2.is_registered = True
        team2.save()
        self.team2 = team2

        # Register user3 to the individual tournament
        self.individual_tournament.user.add(self.user3)
        self.individual_tournament.save()

        # Register user6 to the individual tournament
        self.individual_tournament.user.add(self.user6)
        self.individual_tournament.save()
    
    def test_get_leaderboard_individual_tournament(self):

        # Create activity data for user3
        activity_data_user3 = ActivityData.objects.create(
            user=self.user3,
            activity=self.activity,
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(days=1)).date()
        )
        ActivityMetric.objects.create(
            activity_data=activity_data_user3,
            metric=self.metric_config,
            value=50
        )
        ActivityMetric.objects.create(
            activity_data=activity_data_user3,
            metric=self.metric_config_2,
            value=50
        )

        # Create activity data for user6
        activity_data_user6 = ActivityData.objects.create(
            user=self.user6,
            activity=self.activity,
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(days=1)).date()
        )
        ActivityMetric.objects.create(
            activity_data=activity_data_user6,
            metric=self.metric_config,
            value=150
        )
        ActivityMetric.objects.create(
            activity_data=activity_data_user6,
            metric=self.metric_config_2,
            value=150
        )

        # Get the leaderboard for the team tournament
        url = reverse('get-leaderboard', kwargs={'tournament_id': self.individual_tournament.id})
        params = {
            'start_date': datetime.now().date().isoformat(),
            'end_date': (datetime.now() + timedelta(days=1)).date().isoformat()
        }
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 2)
        self.assertEqual(response.data['data'][0]['rank_holder'], self.user6.username)
        self.assertEqual(response.data['data'][0]['rank'], 1)
        self.assertEqual(response.data['data'][1]['rank_holder'], self.user3.username)
        self.assertEqual(response.data['data'][1]['rank'], 2)
    
    def test_get_leaderboard_individual_tournament_start_end_date(self):
        # Create activity data for user3 outside the date range
        activity_data_user3 = ActivityData.objects.create(
            user=self.user3,
            activity=self.activity,
            start_date=(datetime.now() - timedelta(days=10)).date(),
            end_date=(datetime.now() - timedelta(days=9)).date()
        )
        ActivityMetric.objects.create(
            activity_data=activity_data_user3,
            metric=self.metric_config,
            value=50
        )
        ActivityMetric.objects.create(
            activity_data=activity_data_user3,
            metric=self.metric_config_2,
            value=50
        )

        # Create activity data for user6 within the date range
        activity_data_user6 = ActivityData.objects.create(
            user=self.user6,
            activity=self.activity,
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(days=1)).date()
        )
        ActivityMetric.objects.create(
            activity_data=activity_data_user6,
            metric=self.metric_config,
            value=150
        )
        ActivityMetric.objects.create(
            activity_data=activity_data_user6,
            metric=self.metric_config_2,
            value=150
        )

        # Get the leaderboard for the team tournament with a date range that excludes user3's data
        url = reverse('get-leaderboard', kwargs={'tournament_id': self.individual_tournament.id})
        params = {
            'start_date': (datetime.now()).date().isoformat(),
            'end_date': (datetime.now() + timedelta(days=1)).date().isoformat()
        }
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['rank_holder'], self.user6.username)
        self.assertEqual(response.data['data'][0]['rank'], 1)

        # current_user = self.user6
        # fake_auth_payload = {
        #     'user_id': str(current_user.pk)
        # }
        # from unittest.mock import patch

        # with patch('features.utils.authentication.FirebaseAuthentication.authenticate', return_value=(current_user, fake_auth_payload)):
        #     with patch('features.utils.permissions.IsAdminRole.has_permission', return_value=True):
        #         # Publish the leaderboard
        #         url = reverse('publish-leaderboard', kwargs={'tournament_id': self.individual_tournament.id})
        #         response = self.client.post(url)
        #         self.assertEqual(response.status_code, 201)

        #         # Get the published leaderboard
        #         url = reverse('get-published-leaderboard', kwargs={'tournament_id': self.individual_tournament.id})
        #         response = self.client.get(url)
        #         self.assertEqual(response.status_code, 200)
        #         self.assertEqual(len(response.data['data']), 1)
        #         self.assertEqual(response.data['data'][0]['rank_holder'], self.user6.username)
        #         self.assertEqual(response.data['data'][0]['rank'], 1)
    
    def test_get_leaderboard_team_tournament(self):
        # Create activity data for user1
        activity_data_user1 = ActivityData.objects.create(
            user=self.user1,
            activity=self.activity,
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(days=1)).date()
        )
        ActivityMetric.objects.create(
            activity_data=activity_data_user1,
            metric=self.metric_config,
            value=1000
        )
        ActivityMetric.objects.create(
            activity_data=activity_data_user1,
            metric=self.metric_config_2,
            value=200
        )

        # Create activity data for user2
        activity_data_user2 = ActivityData.objects.create(
            user=self.user2,
            activity=self.activity,
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(days=1)).date()
        )
        ActivityMetric.objects.create(
            activity_data=activity_data_user2,
            metric=self.metric_config,
            value=300
        )
        ActivityMetric.objects.create(
            activity_data=activity_data_user2,
            metric=self.metric_config_2,
            value=100
        )

        # Create activity data for user4
        activity_data_user4 = ActivityData.objects.create(
            user=self.user4,
            activity=self.activity,
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(days=1)).date()
        )
        ActivityMetric.objects.create(
            activity_data=activity_data_user4,
            metric=self.metric_config,
            value=200
        )
        ActivityMetric.objects.create(
            activity_data=activity_data_user4,
            metric=self.metric_config_2,
            value=300
        )

        # Create activity data for user5
        activity_data_user5 = ActivityData.objects.create(
            user=self.user5,
            activity=self.activity,
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(days=1)).date()
        )
        ActivityMetric.objects.create(
            activity_data=activity_data_user5,
            metric=self.metric_config,
            value=400
        )
        ActivityMetric.objects.create(
            activity_data=activity_data_user5,
            metric=self.metric_config_2,
            value=100
        )
        # Get the leaderboard for the team tournament
        url = reverse('get-leaderboard', kwargs={'tournament_id': self.team_tournament.id})
        params = {
            'start_date': datetime.now().date().isoformat(),
            'end_date': (datetime.now() + timedelta(days=1)).date().isoformat()
        }
        response = self.client.get(url, params)
        logger.info(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 2)
        self.assertEqual(response.data['data'][0]['rank_holder'], self.team.name)
        self.assertEqual(response.data['data'][0]['rank'], 1)
        self.assertEqual(response.data['data'][1]['rank_holder'], self.team2.name)
        self.assertEqual(response.data['data'][1]['rank'], 2)