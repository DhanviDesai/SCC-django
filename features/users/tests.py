from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
import datetime

from .models import User
from features.team.models import Team, Invite
from features.activity.models import ActivityData, ActivityConfig
from features.leaderboard.models import Leaderboard
from features.strava.models import StravaUser
from features.tournament.models import Tournament, OnlineIndividualData, TournamentType
from features.season.models import Season
from features.sport.models import Sport
from features.sport_type.models import SportType

class UserDeletionTests(APITestCase):

    def setUp(self):
        self.client = APIClient()

        # Mock Firebase authentication
        self.mock_auth_patch = patch('features.utils.authentication.auth.verify_id_token')
        self.mock_verify_id_token = self.mock_auth_patch.start()
        self.mock_verify_id_token.return_value = {'uid': 'test_admin_uid', 'email': 'admin@example.com', 'roles': ['ADMIN']}

        # Mock Firebase user deletion
        self.mock_delete_user_patch = patch('firebase_admin.auth.delete_user')
        self.mock_delete_user = self.mock_delete_user_patch.start()

        # Create an admin user to perform the deletion
        self.admin_user = User.objects.create(firebase_uid='test_admin_uid', email='admin@example.com', role=['ADMIN'])
        self.client.credentials(HTTP_AUTHORIZATION='Bearer some_token')

        # Create a user to be deleted
        self.user_to_delete = User.objects.create(firebase_uid='test_user_uid', email='test@example.com')

        # Create related objects
        self.team = Team.objects.create(id='a55c232d-c187-432d-9617-4663da73e9f3', name='Test Team', created_by=self.user_to_delete)
        self.team.members.add(self.user_to_delete)

        self.other_user = User.objects.create(firebase_uid='other_user_uid', email='other@example.com')
        self.invite = Invite.objects.create(id="a55c232d-c187-432d-9617-4663da73e9f4", team=self.team, inviter=self.user_to_delete, invitee=self.other_user, created_at=datetime.datetime.now(), updated_at=datetime.datetime.now())

        self.activity_config = ActivityConfig.objects.create(activity_type='Running')
        self.activity_data = ActivityData.objects.create(user=self.user_to_delete, activity=self.activity_config)

        self.season = Season.objects.create(id="a55c232d-c187-432d-9617-4663da73e9f5", name="Test Season", created_at=datetime.date.today(), updated_at=datetime.date.today())
        sport_type = SportType.objects.create(id="a55c232d-c187-432d-9617-4663da73e9f9", name='Test Type')
        self.sport = Sport.objects.create(id="a55c232d-c187-432d-9617-4663da73e9f6", name="Test Sport", sport_type=sport_type, description="Test Description")
        self.tournament_type = TournamentType.objects.create(id="a55c232d-c187-432d-9617-4663da73e9f7", name="Individual Online")
        self.tournament = Tournament.objects.create(id="a55c232d-c187-432d-9617-4663da73e9f8", name='Test Tournament', season=self.season, sport=self.sport, type=self.tournament_type)
        self.tournament.user.add(self.user_to_delete)

        self.leaderboard = Leaderboard.objects.create(tournament=self.tournament, user=self.user_to_delete, rank=1)
        self.online_data = OnlineIndividualData.objects.create(tournament=self.tournament, user=self.user_to_delete)
        self.strava_user = StravaUser.objects.create(user=self.user_to_delete, strava_user_id='12345', access_token='dummy_token', refresh_token='dummy_token', expires_at=1234567890)


    def tearDown(self):
        self.mock_auth_patch.stop()
        self.mock_delete_user_patch.stop()

    def test_delete_user_success(self):
        url = reverse('Delete user', kwargs={'uid': self.user_to_delete.firebase_uid})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.mock_delete_user.assert_called_once_with(self.user_to_delete.firebase_uid)
        self.assertFalse(User.objects.filter(firebase_uid=self.user_to_delete.firebase_uid).exists())

    def test_delete_user_removes_from_team_membership(self):
        self.test_delete_user_success()
        self.team.refresh_from_db()
        self.assertNotIn(self.user_to_delete, self.team.members.all())

    def test_delete_user_sets_team_creator_to_null(self):
        self.test_delete_user_success()
        self.team.refresh_from_db()
        self.assertIsNone(self.team.created_by)

    def test_delete_user_deletes_invites(self):
        self.test_delete_user_success()
        self.assertFalse(Invite.objects.filter(id=self.invite.id).exists())

    def test_delete_user_deletes_activity_data(self):
        self.test_delete_user_success()
        self.assertFalse(ActivityData.objects.filter(id=self.activity_data.id).exists())

    def test_delete_user_sets_leaderboard_user_to_null(self):
        self.test_delete_user_success()
        self.leaderboard.refresh_from_db()
        self.assertIsNone(self.leaderboard.user)

    def test_delete_user_deletes_strava_user(self):
        self.test_delete_user_success()
        self.assertFalse(StravaUser.objects.filter(id=self.strava_user.id).exists())

    def test_delete_user_removes_from_tournament(self):
        self.test_delete_user_success()
        self.tournament.refresh_from_db()
        self.assertNotIn(self.user_to_delete, self.tournament.user.all())

    def test_delete_user_deletes_online_individual_data(self):
        self.test_delete_user_success()
        self.assertFalse(OnlineIndividualData.objects.filter(id=self.online_data.id).exists())
