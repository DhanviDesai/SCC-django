from django.test import TestCase, override_settings

import uuid
from rest_framework import status
from django.urls import reverse
from rest_framework.test import APITestCase
from features.users.models import User
from features.tournament.models import Tournament, TournamentType
from features.season.models import Season
from features.sport.models import Sport
from features.sport_type.models import SportType
from .models import Team, Invite, InviteStatus
from datetime import datetime, timezone

from unittest.mock import patch

# Create your tests here.
@override_settings(GOOGLE_CLOUD_PROJECT='test-project')
class AcceptInviteAPITest(APITestCase):

    def setUp(self):
        # Create users
        self.inviter = User.objects.create(firebase_uid="123", username="123")
        self.invitee = User.objects.create(firebase_uid="abc", username="abc")
        self.other_pending_invitee = User.objects.create(firebase_uid="ghi", username="ghi")
        self.member = User.objects.create(firebase_uid="def", username="def")

        # Create tournament that requires a team of 3
        now = datetime.now(tz=timezone.utc)
        
        # Create a season
        self.season = Season.objects.create(id=uuid.uuid4(), name="season1", created_at=now, updated_at=now)

        # Create a sport type
        self.sport_type = SportType.objects.create(id=uuid.uuid4(), name="1")

        # Create a sport
        self.sport = Sport.objects.create(id=uuid.uuid4(), name="sport1", description="a;djfa", sport_type=self.sport_type)

        # Create a tournament type
        self.tournament_type_team = TournamentType.objects.create(id=uuid.uuid4(), name="Online Team")
        self.tournament_type_individual = TournamentType.objects.create(id=uuid.uuid4(), name="Online Individual")

        # Create a tournament of team type
        self.team_tournament = Tournament.objects.create(
            id=uuid.uuid4(),
            name="tournament1",
            team_size=2,
            season=self.season,
            sport=self.sport,
            type=self.tournament_type_team
        )

        # Create a tournament of individual type
        self.individual_tournament = Tournament.objects.create(
            id=uuid.uuid4(),
            name="tournament2",
            season=self.season,
            sport=self.sport,
            type=self.tournament_type_individual
        )

        # Create a team and add one member
        # self.team = Team.objects.create(id=uuid.uuid4(), name="team1", created_by=self.inviter)
        # self.team.tournament.add(self.team_tournament)
        # self.team.members.add(self.member)

        # # Create two pending invites for this team and tournament
        # self.invite_to_accept = Invite.objects.create(
        #     id=uuid.uuid4(),
        #     team=self.team,
        #     tournament=self.team_tournament,
        #     inviter=self.inviter,
        #     invitee=self.invitee,
        #     status=InviteStatus.PENDING,
        #     created_at=now,
        #     updated_at=now
        # )

        # self.other_pending_invite = Invite.objects.create(
        #     id=uuid.uuid4(),
        #     team=self.team,
        #     tournament=self.team_tournament,
        #     inviter=self.inviter,
        #     invitee=self.other_pending_invitee,
        #     status=InviteStatus.PENDING,
        #     created_at=now,
        #     updated_at=now
        # )

    @patch('features.utils.messaging.send_fcm_notification', return_value=True)
    @patch('features.utils.authentication.FirebaseAuthentication.authenticate')
    def test_create_team(self, mock_authenticate, mock_send_fcm):
        """
        Tests that the team is created correctly.
        """
        current_user = self.inviter

        fake_auth_payload = {
            'user_id': str(current_user.pk)
        }

        mock_authenticate.return_value = (current_user, fake_auth_payload)

        url = reverse('create-team')
        data = {
            'team_name': 'Test Team',
            'tournament_id': str(self.team_tournament.id)
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Team.objects.count(), 1)
        self.assertEqual(response.data.get('data').get('name'), 'Test Team')
        self.assertEqual(len(response.data.get('data').get('members')), 1)
    
    @patch('features.utils.messaging.send_fcm_notification', return_value=True)
    @patch('features.utils.authentication.FirebaseAuthentication.authenticate')
    def test_user_create_another_team(self, mock_authenticate, mock_send_fcm):
        """
        Tests that a user cannot create another team for the same tournament.
        """
        current_user = self.inviter

        fake_auth_payload = {
            'user_id': str(current_user.pk)
        }

        mock_authenticate.return_value = (current_user, fake_auth_payload)

        # Create the first team
        url = reverse('create-team')
        data = {
            'team_name': 'Test Team 1',
            'tournament_id': str(self.team_tournament.id)
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Attempt to create another team for the same tournament
        data['team_name'] = 'Test Team 2'
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'You have already created a team for this tournament')

    @patch('features.utils.messaging.send_fcm_notification', return_value=True)
    @patch('features.utils.authentication.FirebaseAuthentication.authenticate')
    def test_create_team_for_individual_tournament(self, mock_authenticate, mock_send_fcm):
        """
        Tests that the team should not be created if the tournament is not of team type.
        """
        current_user = self.inviter

        fake_auth_payload = {
            'user_id': str(current_user.pk)
        }

        mock_authenticate.return_value = (current_user, fake_auth_payload)

        url = reverse('create-team')
        data = {
            'team_name': 'Test Team',
            'tournament_id': str(self.individual_tournament.id)
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('features.utils.messaging.send_fcm_notification', return_value=True)
    @patch('features.utils.authentication.FirebaseAuthentication.authenticate')
    def test_invite_user(self, mock_authenticate, mock_send_fcm):
        """
        Tests that a user can be invited to a team.
        """
        current_user = self.inviter
        fake_auth_payload = {
            'user_id': str(current_user.pk)
        }
        mock_authenticate.return_value = (current_user, fake_auth_payload)

        # Create a team via model
        team = Team.objects.create(id=uuid.uuid4(), name="Test Team", created_by=self.inviter)
        team.tournament.add(self.team_tournament)
        team.members.add(self.inviter)

        # Invite a user to the team
        url = reverse('invite-user', kwargs={'team_id': team.id})
        data = {
            'user_id': self.invitee.firebase_uid,
            "tournament_id": str(self.team_tournament.id)
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['inviter'], self.inviter.firebase_uid)
        self.assertEqual(response.data['data']['team']['id'], str(team.id))
        self.assertEqual(response.data['data']['team']['name'], team.name)
        self.assertEqual(response.data['data']['invitee'], self.invitee.firebase_uid)
        self.assertEqual(response.data['data']['status'], InviteStatus.PENDING)
    
    @patch('features.utils.messaging.send_fcm_notification', return_value=True)
    @patch('features.utils.authentication.FirebaseAuthentication.authenticate')
    def test_invite_user_again(self, mock_authenticate, mock_send_fcm):
        """
        Tests that a user cannot invite the same user again.
        """
        current_user = self.inviter
        fake_auth_payload = {
            'user_id': str(current_user.pk)
        }
        mock_authenticate.return_value = (current_user, fake_auth_payload)

        # Create a team
        url = reverse('create-team')
        data = {
            'team_name': 'Test Team',
            'tournament_id': str(self.team_tournament.id)
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        team = response.data.get('data')

        # Invite the user to the team
        url = reverse('invite-user', kwargs={'team_id': team['id']})
        data = {
            'user_id': self.invitee.firebase_uid,
            "tournament_id": str(self.team_tournament.id)
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Attempt to invite the same user again
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('User has already been invited', response.data['message'])

    @patch('features.utils.messaging.send_fcm_notification', return_value=True)
    @patch('features.utils.authentication.FirebaseAuthentication.authenticate')
    def test_inviter_is_created_by(self, mock_authenticate, mock_send_fcm):
        """
        Tests that the inviter is the creator of the team.
        """
        current_user = self.inviter
        fake_auth_payload = {
            'user_id': str(current_user.pk)
        }
        mock_authenticate.return_value = (current_user, fake_auth_payload)

        # Create a team
        url = reverse('create-team')
        data = {
            'team_name': 'Test Team',
            'tournament_id': str(self.team_tournament.id)
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        team = response.data.get('data')

        # Invite a user to the team
        url = reverse('invite-user', kwargs={'team_id': team['id']})
        data = {
            'user_id': self.invitee.firebase_uid,
            "tournament_id": str(self.team_tournament.id)
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['inviter'], self.inviter.firebase_uid)

    @patch('features.utils.messaging.send_fcm_notification', return_value=True)
    @patch('features.utils.authentication.FirebaseAuthentication.authenticate')
    def test_invite_already_member(self, mock_authenticate, mock_send_fcm):
        """
        Tests that a user cannot invite a member who is already in the team.
        """
        current_user = self.inviter
        fake_auth_payload = {
            'user_id': str(current_user.pk)
        }
        mock_authenticate.return_value = (current_user, fake_auth_payload)

        # Create a team
        url = reverse('create-team')
        data = {
            'team_name': 'Test Team',
            'tournament_id': str(self.team_tournament.id)
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        team =  response.data.get('data')

        # Invite a user who is already a member of the team
        url = reverse('invite-user', kwargs={'team_id': team['id']})
        data = {
            'user_id': str(self.inviter.pk),
            'tournament_id': str(self.team_tournament.pk)
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('User is already a member of the team', response.data['message'])
    
    @patch('features.utils.messaging.send_fcm_notification', return_value=True)
    @patch('features.utils.authentication.FirebaseAuthentication.authenticate')
    def test_accept_invite(self, mock_authenticate, mock_send_fcm):
        """
        Tests that a user can accept an invite and is added to the team.
        """

        # Create a team via model
        team = Team.objects.create(id=uuid.uuid4(), name="Test Team", created_by=self.inviter)
        team.tournament.add(self.team_tournament)
        team.members.add(self.inviter)
        team.save()
        
        # Create an invite to the team via model
        invite = Invite.objects.create(
            id=uuid.uuid4(),
            team=team,
            tournament=self.team_tournament,
            inviter=self.inviter,
            invitee=self.invitee,
            status=InviteStatus.PENDING,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc)
        )

        current_user = self.invitee
        fake_auth_payload = {
            'user_id': str(current_user.pk)
        }
        mock_authenticate.return_value = (current_user, fake_auth_payload)

        # Accept the invite
        url = reverse('accept-invite', kwargs={'invite_id': invite.id})
        response = self.client.put(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        team.refresh_from_db()
        self.assertIn(self.invitee, team.members.all())
        self.assertTrue(team.is_registered)
        self.assertEqual(team.members.count(), 2)
        invite.refresh_from_db()
        self.assertEqual(invite.status, InviteStatus.ACCEPTED)

    # def test_accept_invite_not_pending(self):
    # def test_accept_invite_after_team_full(self):
    # def test_accept_invite_invalid(self):


    
    # def test_invite_non_existent_user(self):
    #     """
    #     Tests that a user cannot invite a non-existent user.
    #     """
    #     url = reverse('invite-user', kwargs={'team_id': self.team.id})
    #     data = {
    #         'invitee_firebase_uid': 'non_existent_uid'
    #     }
    #     response = self.client.post(url, data)

    #     self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    #     self.assertIn('User not found.', response.data['error'])
    
    # @patch('features.utils.messaging.send_fcm_notification', return_value=True)
    # @patch('features.utils.authentication.FirebaseAuthentication.authenticate')
    # def test_accept_invite_success_team_not_full(self, mock_authenticate, mock_send_fcm):
    #     """
    #     Tests the happy path: A user accepts, is added, but the team is not yet full.
    #     Team needs 3, has 1 member. After this, it will have 2
    #     """
    #     current_user = self.invitee

    #     fake_auth_payload = {
    #         'user_id': str(current_user.pk)
    #     }

    #     mock_authenticate.return_value = (current_user, fake_auth_payload)

    #     url = reverse('accept-invite', kwargs={'invite_id': self.invite_to_accept.id})
    #     response = self.client.put(url)

    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.team.refresh_from_db()
    #     self.assertIn(self.invitee, self.team.members.all())
    #     self.assertEqual(self.team.members.count(), 2)
    
    # @patch('features.utils.messaging.send_fcm_notification', return_value=True)
    # @patch('features.utils.authentication.FirebaseAuthentication.authenticate')
    # def test_accept_invite_makes_team_full(self, mock_authenticate, mock_send_fcm):
    #     """Tests the final member joining with mocked authentication."""
    #     # Configure the mock to "log in" the user accepting the invite
    #     current_user = self.invitee

    #     fake_auth_payload = {
    #         'user_id': str(current_user.pk)
    #     }

    #     mock_authenticate.return_value = (current_user, fake_auth_payload)
        
    #     # Add another member manually to make the team size 2
    #     another_member = User.objects.create(firebase_uid="789", username="789")
    #     self.team.members.add(another_member)
        
    #     url = reverse('accept-invite', kwargs={'invite_id': self.invite_to_accept.id})
    #     response = self.client.put(url)

    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.team.refresh_from_db()
    #     self.other_pending_invite.refresh_from_db()
    #     self.assertEqual(self.team.members.count(), 3)
    #     self.assertTrue(self.team.is_registered)
    #     self.assertEqual(self.other_pending_invite.status, InviteStatus.EXPIRED)

