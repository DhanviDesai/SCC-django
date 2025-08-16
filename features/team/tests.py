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
from datetime import datetime

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
        now = datetime.now()
        self.season = Season.objects.create(id=uuid.uuid4(), name="season1", created_at=now, updated_at=now)
        self.sport_type = SportType.objects.create(id=uuid.uuid4(), name="1")
        self.sport = Sport.objects.create(id=uuid.uuid4(), name="sport1", description="a;djfa", sport_type=self.sport_type)
        self.tournament_type = TournamentType.objects.create(id=uuid.uuid4(), name="team")
        self.tournament = Tournament.objects.create(
            id=uuid.uuid4(),
            name="tournament1",
            team_size=3,
            season=self.season,
            sport=self.sport,
            type=self.tournament_type
        )

        # Create a team and add one member
        self.team = Team.objects.create(id=uuid.uuid4(), name="team1", created_by=self.inviter)
        self.team.tournament.add(self.tournament)
        self.team.members.add(self.member)

        # Create two pending invites for this team and tournament
        self.invite_to_accept = Invite.objects.create(
            id=uuid.uuid4(),
            team=self.team,
            tournament=self.tournament,
            inviter=self.inviter,
            invitee=self.invitee,
            status=InviteStatus.PENDING,
            created_at=now,
            updated_at=now
        )

        self.other_pending_invite = Invite.objects.create(
            id=uuid.uuid4(),
            team=self.team,
            tournament=self.tournament,
            inviter=self.inviter,
            invitee=self.other_pending_invitee,
            status=InviteStatus.PENDING,
            created_at=now,
            updated_at=now
        )

    @patch('features.utils.messaging.send_fcm_notification', return_value=True)
    @patch('features.utils.authentication.FirebaseAuthentication.authenticate')
    def test_accept_invite_success_team_not_full(self, mock_authenticate, mock_send_fcm):
        """
        Tests the happy path: A user accepts, is added, but the team is not yet full.
        Team needs 3, has 1 member. After this, it will have 2
        """
        current_user = self.invitee

        fake_auth_payload = {
            'user_id': str(current_user.pk)
        }

        mock_authenticate.return_value = (current_user, fake_auth_payload)

        url = reverse('accept-invite', kwargs={'invite_id': self.invite_to_accept.id})
        response = self.client.put(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.team.refresh_from_db()
        self.assertIn(self.invitee, self.team.members.all())
        self.assertEqual(self.team.members.count(), 2)
    
    @patch('features.utils.messaging.send_fcm_notification', return_value=True)
    @patch('features.utils.authentication.FirebaseAuthentication.authenticate')
    def test_accept_invite_makes_team_full(self, mock_authenticate, mock_send_fcm):
        """Tests the final member joining with mocked authentication."""
        # Configure the mock to "log in" the user accepting the invite
        current_user = self.invitee

        fake_auth_payload = {
            'user_id': str(current_user.pk)
        }

        mock_authenticate.return_value = (current_user, fake_auth_payload)
        
        # Add another member manually to make the team size 2
        another_member = User.objects.create(firebase_uid="789", username="789")
        self.team.members.add(another_member)
        
        url = reverse('accept-invite', kwargs={'invite_id': self.invite_to_accept.id})
        response = self.client.put(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.team.refresh_from_db()
        self.other_pending_invite.refresh_from_db()
        self.assertEqual(self.team.members.count(), 3)
        self.assertTrue(self.team.is_registered)
        self.assertEqual(self.other_pending_invite.status, InviteStatus.EXPIRED)

