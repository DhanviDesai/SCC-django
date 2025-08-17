from django.test import TestCase
from .models import Leaderboard
from features.users.models import User
from features.tournament.models import Tournament, TournamentType
from features.season.models import Season
from features.sport.models import Sport, SportType
import uuid

import datetime

class LeaderboardTestCase(TestCase):
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
        self.tournament = Tournament.objects.create(
            id=uuid.uuid4(),
            name="Test Tournament",
            season=self.season,
            sport=self.sport,
            type=self.tournament_type
        )
        self.tournament.user.add(self.user)

    def test_leaderboard_creation(self):
        leaderboard_entry = Leaderboard.objects.create(
            user=self.user,
            tournament=self.tournament,
            total_distance=100,
            total_moving_time=3600,
            total_elevation_gain=500,
            activity_count=1
        )
        self.assertEqual(Leaderboard.objects.count(), 1)
        self.assertEqual(leaderboard_entry.user, self.user)
        self.assertEqual(leaderboard_entry.tournament, self.tournament)
