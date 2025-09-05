import uuid
from unittest.mock import patch
from rest_framework.test import APITestCase
from rest_framework import status
import datetime
from features.users.models import User
from features.sport.models import Sport
from features.sport_type.models import SportType
from features.season.models import Season
from features.city.models import City
from features.tournament.models import TournamentType, Tournament, TournamentStatus
from features.activity.models import ActivityConfig
from features.utils.response_wrapper import error_response

class TournamentTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.all().delete()
        Season.objects.all().delete()
        City.objects.all().delete()
        Sport.objects.all().delete()
        SportType.objects.all().delete()
        TournamentType.objects.all().delete()
        Tournament.objects.all().delete()
        ActivityConfig.objects.all().delete()
        cls.admin_user = User.objects.create(
            firebase_uid=str(uuid.uuid4()),
            username='adminuser',
            email='admin@example.com',
            role=['ADMIN']
        )
        cls.user = User.objects.create(
            firebase_uid=str(uuid.uuid4()),
            username='testuser',
            email='test@example.com',
            role=['USER']
        )

        cls.sport_type = SportType.objects.create(id=uuid.uuid4(), name='Test Sport Type')
        cls.sport = Sport.objects.create(id=uuid.uuid4(), name='Test Sport', sport_type=cls.sport_type, description="Test Description")
        today = datetime.date.today()
        cls.season = Season.objects.create(
            id=uuid.uuid4(),
            name='Test Season',
            start_date='2025-01-01',
            end_date='2025-12-31',
            created_at=today - datetime.timedelta(days=1),
            updated_at=today - datetime.timedelta(days=1)
        )
        cls.individual_type = TournamentType.objects.create(id=uuid.uuid4(), name='Individual On-Ground')
        cls.team_type = TournamentType.objects.create(id=uuid.uuid4(), name='Team On-Ground')
        cls.online_individual_type = TournamentType.objects.create(id=uuid.uuid4(), name='Individual Online')

        cls.tournament = Tournament.objects.create(
            id=uuid.uuid4(),
            name='Test Tournament 1',
            season=cls.season,
            sport=cls.sport,
            type=cls.individual_type,
        )

        cls.season2 = Season.objects.create(
            id=uuid.uuid4(),
            name='Test Season 2',
            start_date='2026-01-01',
            end_date='2026-12-31',
            created_at=today,
            updated_at=today
        )
        cls.tournament2 = Tournament.objects.create(
            id=uuid.uuid4(),
            name='Test Tournament 2',
            season=cls.season2,
            sport=cls.sport,
            type=cls.individual_type,
        )
        cls.city1 = City.objects.create(id=uuid.uuid4(), name='Test City 1')
        cls.city2 = City.objects.create(id=uuid.uuid4(), name='Test City 2')
        cls.activity_config = ActivityConfig.objects.create(activity_type='Test Activity')

        cls.tournament.cities.add(cls.city1, cls.city2)

    def test_list_tournament_types(self):
        url = '/api/tournament/type'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 3)

    def test_list_tournaments_default_season(self):
        url = '/api/tournament/list'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Tournament 2')

    def test_list_tournaments_filter_by_season(self):
        url = f'/api/tournament/list?season_id={self.season.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Tournament 1')

    def test_list_tournaments_pagination(self):
        # Create more tournaments to test pagination
        for i in range(10):
            Tournament.objects.create(
                id=uuid.uuid4(),
                name=f'Paging Test Tournament {i}',
                season=self.season2,
                sport=self.sport,
                type=self.individual_type,
            )
        url = '/api/tournament/list'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)
        self.assertIn('next', response.data)

    def test_list_tournaments_filter_by_name(self):
        url = f'/api/tournament/list?season_id={self.season2.id}&search=Test%20Tournament%202'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Tournament 2')

    @patch('features.tournament.views.FirebaseAuthentication.authenticate')
    def test_add_tournament_admin(self, mock_authenticate):
        fake_auth_payload = {'user_id': self.admin_user.firebase_uid, 'uid': self.admin_user.firebase_uid, 'role': ['ADMIN']}
        mock_authenticate.return_value = (self.admin_user, fake_auth_payload)

        url = '/api/tournament/add'
        data = {
            'name': 'New Test Tournament',
            'type': str(self.individual_type.id),
            'sport': str(self.sport.id),
            'city': [str(self.city1.id), str(self.city2.id)],
            'season': str(self.season.id),
            'registration_start_date': '2025-03-01',
            'registration_end_date': '2025-03-31',
            'start_date': '2025-04-10',
            'end_date': '2025-04-20',
            'description': 'A new tournament for testing.'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @patch('features.tournament.views.FirebaseAuthentication.authenticate')
    def test_add_tournament_non_admin(self, mock_authenticate):
        fake_auth_payload = {'user_id': self.user.firebase_uid, 'uid': self.user.firebase_uid, 'role': []}
        mock_authenticate.return_value = (self.user, fake_auth_payload)

        url = '/api/tournament/add'
        data = {}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('features.tournament.views.FirebaseAuthentication.authenticate')
    def test_add_tournament_missing_name(self, mock_authenticate):
        fake_auth_payload = {'user_id': self.admin_user.firebase_uid, 'uid': self.admin_user.firebase_uid, 'role': ['ADMIN']}
        mock_authenticate.return_value = (self.admin_user, fake_auth_payload)

        url = '/api/tournament/add'
        data = {
            'type': str(self.individual_type.id),
            'sport': str(self.sport.id),
            'city': [str(self.city1.id)],
            'season': str(self.season.id),
            'registration_start_date': '2025-03-01',
            'registration_end_date': '2025-03-31',
            'start_date': '2025-04-10',
            'end_date': '2025-04-20',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Name cannot be null', response.data['message'])

    @patch('features.tournament.views.FirebaseAuthentication.authenticate')
    def test_add_team_tournament_requires_team_size(self, mock_authenticate):
        fake_auth_payload = {'user_id': self.admin_user.firebase_uid, 'uid': self.admin_user.firebase_uid, 'role': ['ADMIN']}
        mock_authenticate.return_value = (self.admin_user, fake_auth_payload)

        url = '/api/tournament/add'
        data = {
            'name': 'Team Tournament without team size',
            'type': str(self.team_type.id),
            'sport': str(self.sport.id),
            'city': [str(self.city1.id)],
            'season': str(self.season.id),
            'registration_start_date': '2025-03-01',
            'registration_end_date': '2025-03-31',
            'start_date': '2025-04-10',
            'end_date': '2025-04-20',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Team size cannot be null', response.data['message'])

    @patch('features.tournament.views.FirebaseAuthentication.authenticate')
    def test_add_online_tournament_requires_activity(self, mock_authenticate):
        fake_auth_payload = {'user_id': self.admin_user.firebase_uid, 'uid': self.admin_user.firebase_uid, 'role': ['ADMIN']}
        mock_authenticate.return_value = (self.admin_user, fake_auth_payload)

        url = '/api/tournament/add'
        data = {
            'name': 'Online Tournament without activity',
            'type': str(self.online_individual_type.id),
            'sport': str(self.sport.id),
            'city': [str(self.city1.id)],
            'season': str(self.season.id),
            'registration_start_date': '2025-03-01',
            'registration_end_date': '2025-03-31',
            'start_date': '2025-04-10',
            'end_date': '2025-04-20',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Online tournaments must have an activity associated', response.data['message'])

    @patch('features.tournament.views.FirebaseAuthentication.authenticate')
    def test_list_all_tournaments_admin(self, mock_authenticate):
        fake_auth_payload = {'user_id': self.admin_user.firebase_uid, 'uid': self.admin_user.firebase_uid, 'role': ['ADMIN']}
        mock_authenticate.return_value = (self.admin_user, fake_auth_payload)

        url = f'/api/tournament/list/all?season_id={self.season.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)

    @patch('features.tournament.views.FirebaseAuthentication.authenticate')
    def test_list_all_tournaments_non_admin(self, mock_authenticate):
        fake_auth_payload = {'user_id': self.user.firebase_uid, 'uid': self.user.firebase_uid, 'role': []}
        mock_authenticate.return_value = (self.user, fake_auth_payload)

        url = f'/api/tournament/list/all?season_id={self.season.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('features.tournament.views.FirebaseAuthentication.authenticate')
    def test_add_schedule_admin(self, mock_authenticate):
        fake_auth_payload = {'user_id': self.admin_user.firebase_uid, 'uid': self.admin_user.firebase_uid, 'role': ['ADMIN']}
        mock_authenticate.return_value = (self.admin_user, fake_auth_payload)

        url = '/api/tournament/schedule/add'
        data = {
            'tournament_id': str(self.tournament.id),
            'file_url': 'http://example.com/schedule.pdf'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.tournament.refresh_from_db()
        self.assertEqual(self.tournament.schedule, 'http://example.com/schedule.pdf')

    @patch('features.tournament.views.FirebaseAuthentication.authenticate')
    def test_add_schedule_non_admin(self, mock_authenticate):
        fake_auth_payload = {'user_id': self.user.firebase_uid, 'uid': self.user.firebase_uid, 'role': []}
        mock_authenticate.return_value = (self.user, fake_auth_payload)

        url = '/api/tournament/schedule/add'
        data = {
            'tournament_id': str(self.tournament.id),
            'file_url': 'http://example.com/schedule.pdf'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('features.tournament.views.FirebaseAuthentication.authenticate')
    def test_add_schedule_missing_data(self, mock_authenticate):
        fake_auth_payload = {'user_id': self.admin_user.firebase_uid, 'uid': self.admin_user.firebase_uid, 'role': ['ADMIN']}
        mock_authenticate.return_value = (self.admin_user, fake_auth_payload)

        url = '/api/tournament/schedule/add'
        # Missing file_url
        data = {'tournament_id': str(self.tournament.id)}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Missing tournament_id
        data = {'file_url': 'http://example.com/schedule.pdf'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('features.tournament.views.FirebaseAuthentication.authenticate')
    def test_add_schedule_non_existent_tournament(self, mock_authenticate):
        fake_auth_payload = {'user_id': self.admin_user.firebase_uid, 'uid': self.admin_user.firebase_uid, 'role': ['ADMIN']}
        mock_authenticate.return_value = (self.admin_user, fake_auth_payload)

        url = '/api/tournament/schedule/add'
        data = {
            'tournament_id': str(uuid.uuid4()),
            'file_url': 'http://example.com/schedule.pdf'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('features.tournament.views.generate_presigned_url', return_value=('http://presigned-url.com', 'http://public-url.com'))
    @patch('features.tournament.views.FirebaseAuthentication.authenticate')
    def test_get_presigned_url_admin(self, mock_authenticate, mock_generate_url):
        fake_auth_payload = {'user_id': self.admin_user.firebase_uid, 'uid': self.admin_user.firebase_uid, 'role': ['ADMIN']}
        mock_authenticate.return_value = (self.admin_user, fake_auth_payload)

        url = '/api/tournament/schedule/presigned-url?filename=test.pdf&filetype=application/pdf'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['presigned_url'], 'http://presigned-url.com')

    @patch('features.tournament.views.FirebaseAuthentication.authenticate')
    def test_get_presigned_url_non_admin(self, mock_authenticate):
        fake_auth_payload = {'user_id': self.user.firebase_uid, 'uid': self.user.firebase_uid, 'role': []}
        mock_authenticate.return_value = (self.user, fake_auth_payload)

        url = '/api/tournament/schedule/presigned-url?filename=test.pdf&filetype=application/pdf'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('features.tournament.views.FirebaseAuthentication.authenticate')
    def test_get_tournament_by_id(self, mock_authenticate):
        fake_auth_payload = {'user_id': self.user.firebase_uid, 'uid': self.user.firebase_uid, 'role': []}
        mock_authenticate.return_value = (self.user, fake_auth_payload)

        url = f'/api/tournament/{self.tournament.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['name'], self.tournament.name)

    @patch('features.tournament.views.FirebaseAuthentication.authenticate')
    def test_get_non_existent_tournament(self, mock_authenticate):
        fake_auth_payload = {'user_id': self.user.firebase_uid, 'uid': self.user.firebase_uid, 'role': []}
        mock_authenticate.return_value = (self.user, fake_auth_payload)

        url = f'/api/tournament/{uuid.uuid4()}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('features.tournament.views.FirebaseAuthentication.authenticate')
    def test_update_tournament_by_admin(self, mock_authenticate):
        fake_auth_payload = {'user_id': self.admin_user.firebase_uid, 'uid': self.admin_user.firebase_uid, 'role': ['ADMIN']}
        mock_authenticate.return_value = (self.admin_user, fake_auth_payload)

        url = f'/api/tournament/{self.tournament.id}'
        data = {'name': 'Updated Tournament Name'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.tournament.refresh_from_db()
        self.assertEqual(self.tournament.name, 'Updated Tournament Name')

    @patch('features.tournament.views.FirebaseAuthentication.authenticate')
    def test_update_tournament_by_non_admin(self, mock_authenticate):
        fake_auth_payload = {'user_id': self.user.firebase_uid, 'uid': self.user.firebase_uid, 'role': []}
        mock_authenticate.return_value = (self.user, fake_auth_payload)

        url = f'/api/tournament/{self.tournament.id}'
        data = {'name': 'Updated by Non-Admin'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('features.tournament.views.FirebaseAuthentication.authenticate')
    def test_update_non_existent_tournament(self, mock_authenticate):
        fake_auth_payload = {'user_id': self.admin_user.firebase_uid, 'uid': self.admin_user.firebase_uid, 'role': ['ADMIN']}
        mock_authenticate.return_value = (self.admin_user, fake_auth_payload)

        url = f'/api/tournament/{uuid.uuid4()}'
        data = {'name': 'This should fail'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('features.tournament.views.FirebaseAuthentication.authenticate')
    def test_update_team_tournament_team_size(self, mock_authenticate):
        fake_auth_payload = {'user_id': self.admin_user.firebase_uid, 'uid': self.admin_user.firebase_uid, 'role': ['ADMIN']}
        mock_authenticate.return_value = (self.admin_user, fake_auth_payload)

        team_tournament = Tournament.objects.create(
            id=uuid.uuid4(),
            name='Team Tournament',
            season=self.season,
            sport=self.sport,
            type=self.team_type,
            team_size=4
        )

        url = f'/api/tournament/{team_tournament.id}'
        data = {'team_size': 5}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        team_tournament.refresh_from_db()
        self.assertEqual(team_tournament.team_size, 5)

    @patch('features.tournament.views.FirebaseAuthentication.authenticate')
    def test_update_online_tournament_activity(self, mock_authenticate):
        fake_auth_payload = {'user_id': self.admin_user.firebase_uid, 'uid': self.admin_user.firebase_uid, 'role': ['ADMIN']}
        mock_authenticate.return_value = (self.admin_user, fake_auth_payload)

        online_tournament = Tournament.objects.create(
            id=uuid.uuid4(),
            name='Online Tournament',
            season=self.season,
            sport=self.sport,
            type=self.online_individual_type,
            activity=self.activity_config
        )
        new_activity_config = ActivityConfig.objects.create(activity_type='New Test Activity')

        url = f'/api/tournament/{online_tournament.id}'
        data = {'activity': new_activity_config.id}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        online_tournament.refresh_from_db()
        self.assertEqual(online_tournament.activity, new_activity_config)

    @patch('features.tournament.views.FirebaseAuthentication.authenticate')
    def test_delete_tournament_admin(self, mock_authenticate):
        fake_auth_payload = {'user_id': self.admin_user.firebase_uid, 'uid': self.admin_user.firebase_uid, 'role': ['ADMIN']}
        mock_authenticate.return_value = (self.admin_user, fake_auth_payload)

        url = f'/api/tournament/delete/{self.tournament.id}'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.tournament.refresh_from_db()
        self.assertEqual(self.tournament.status, TournamentStatus.DELETED)

    @patch('features.tournament.views.FirebaseAuthentication.authenticate')
    def test_delete_tournament_non_admin(self, mock_authenticate):
        fake_auth_payload = {'user_id': self.user.firebase_uid, 'uid': self.user.firebase_uid, 'role': []}
        mock_authenticate.return_value = (self.user, fake_auth_payload)

        url = f'/api/tournament/delete/{self.tournament.id}'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('features.tournament.views.FirebaseAuthentication.authenticate')
    def test_delete_non_existent_tournament(self, mock_authenticate):
        fake_auth_payload = {'user_id': self.admin_user.firebase_uid, 'uid': self.admin_user.firebase_uid, 'role': ['ADMIN']}
        mock_authenticate.return_value = (self.admin_user, fake_auth_payload)

        url = f'/api/tournament/delete/{uuid.uuid4()}'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('features.tournament.views.FirebaseAuthentication.authenticate')
    def test_register_for_individual_tournament(self, mock_authenticate):
        fake_auth_payload = {'user_id': self.user.firebase_uid, 'uid': self.user.firebase_uid, 'role': []}
        mock_authenticate.return_value = (self.user, fake_auth_payload)

        url = f'/api/tournament/register/{self.tournament.id}'
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.tournament.refresh_from_db()
        self.assertIn(self.user, self.tournament.user.all())

    @patch('features.tournament.views.FirebaseAuthentication.authenticate')
    def test_register_for_team_tournament_fails(self, mock_authenticate):
        fake_auth_payload = {'user_id': self.user.firebase_uid, 'uid': self.user.firebase_uid, 'role': []}
        mock_authenticate.return_value = (self.user, fake_auth_payload)

        team_tournament = Tournament.objects.create(
            id=uuid.uuid4(),
            name='Team Tournament',
            season=self.season,
            sport=self.sport,
            type=self.team_type,
        )

        url = f'/api/tournament/register/{team_tournament.id}'
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('features.tournament.views.FirebaseAuthentication.authenticate')
    def test_register_for_same_tournament_twice_fails(self, mock_authenticate):
        fake_auth_payload = {'user_id': self.user.firebase_uid, 'uid': self.user.firebase_uid, 'role': []}
        mock_authenticate.return_value = (self.user, fake_auth_payload)

        # First registration
        url = f'/api/tournament/register/{self.tournament.id}'
        self.client.put(url)

        # Second registration
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('features.tournament.views.FirebaseAuthentication.authenticate')
    def test_register_for_non_existent_tournament(self, mock_authenticate):
        fake_auth_payload = {'user_id': self.user.firebase_uid, 'uid': self.user.firebase_uid, 'role': []}
        mock_authenticate.return_value = (self.user, fake_auth_payload)

        url = f'/api/tournament/register/{uuid.uuid4()}'
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('features.tournament.views.FirebaseAuthentication.authenticate')
    def test_list_registrants(self, mock_authenticate):
        fake_auth_payload = {'user_id': self.user.firebase_uid, 'uid': self.user.firebase_uid, 'role': []}
        mock_authenticate.return_value = (self.user, fake_auth_payload)

        self.tournament.user.add(self.user)
        url = f'/api/tournament/list/{self.tournament.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)

    def test_list_registrants_unauthenticated(self):
        url = f'/api/tournament/list/{self.tournament.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('features.tournament.views.FirebaseAuthentication.authenticate')
    def test_submit_data_for_online_tournament(self, mock_authenticate):
        fake_auth_payload = {'user_id': self.user.firebase_uid, 'uid': self.user.firebase_uid, 'role': []}
        mock_authenticate.return_value = (self.user, fake_auth_payload)

        online_tournament = Tournament.objects.create(
            id=uuid.uuid4(),
            name='Online Tournament Data',
            season=self.season,
            sport=self.sport,
            type=self.online_individual_type,
        )
        online_tournament.user.add(self.user)

        url = f'/api/tournament/submit/{online_tournament.id}'
        data = {
            'data': [
                {'date': '2025-05-01', 'count': 100},
                {'date': '2025-05-02', 'count': 150},
            ]
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('features.tournament.views.FirebaseAuthentication.authenticate')
    def test_submit_data_unregistered_user(self, mock_authenticate):
        fake_auth_payload = {'user_id': self.user.firebase_uid, 'uid': self.user.firebase_uid, 'role': []}
        mock_authenticate.return_value = (self.user, fake_auth_payload)

        online_tournament = Tournament.objects.create(
            id=uuid.uuid4(),
            name='Online Tournament Data',
            season=self.season,
            sport=self.sport,
            type=self.online_individual_type,
        )

        url = f'/api/tournament/submit/{online_tournament.id}'
        data = {'data': []}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('features.tournament.views.FirebaseAuthentication.authenticate')
    def test_submit_data_for_non_online_tournament(self, mock_authenticate):
        fake_auth_payload = {'user_id': self.user.firebase_uid, 'uid': self.user.firebase_uid, 'role': []}
        mock_authenticate.return_value = (self.user, fake_auth_payload)

        url = f'/api/tournament/submit/{self.tournament.id}'
        data = {'data': []}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('features.tournament.views.FirebaseAuthentication.authenticate')
    def test_submit_data_missing_data(self, mock_authenticate):
        fake_auth_payload = {'user_id': self.user.firebase_uid, 'uid': self.user.firebase_uid, 'role': []}
        mock_authenticate.return_value = (self.user, fake_auth_payload)

        online_tournament = Tournament.objects.create(
            id=uuid.uuid4(),
            name='Online Tournament Data',
            season=self.season,
            sport=self.sport,
            type=self.online_individual_type,
        )
        online_tournament.user.add(self.user)

        url = f'/api/tournament/submit/{online_tournament.id}'
        data = {}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
