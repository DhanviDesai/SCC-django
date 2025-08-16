from django.test import TestCase
from rest_framework.test import APITestCase

import uuid
from datetime import datetime

from features.users.models import User
from features.sport.models import Sport, SportType
from features.season.models import Season
from features.tournament.models import Tournament, TournamentType

from unittest.mock import patch

# Create your tests here.
class RegisterTournamentAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create(firebase_uid='123', username="123")

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
    
    @patch('features.utils.authentication.FirebaseAuthentication.authenticate')
    def test_register_tournament(self, mock_authenticate):
        """
        """
