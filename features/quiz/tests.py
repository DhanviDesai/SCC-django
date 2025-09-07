from rest_framework.test import APITestCase
from django.urls import reverse
from unittest.mock import patch
from features.users.models import User
from features.tournament.models import Tournament, TournamentType
from features.season.models import Season
from features.sport.models import Sport, SportType
from .models import Question, QuizRound, QuizResult, UserQuizAttempt, QuestionPool
import uuid
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)

class QuizTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create(firebase_uid="test_user_uid", username="test_user", role=['USER'])
        self.admin_user = User.objects.create(firebase_uid="test_admin_uid", username="test_admin", role=['ADMIN'])

        self.quiz_tournament_type, _ = TournamentType.objects.get_or_create(name='Quiz', defaults={'id': uuid.uuid4()})
        now = datetime.now(tz=timezone.utc)
        self.season = Season.objects.create(id=uuid.uuid4(), name="Test Season", created_at=now, updated_at=now)
        self.sport_type = SportType.objects.create(id=uuid.uuid4(), name="Test Sport Type")
        self.sport = Sport.objects.create(id=uuid.uuid4(), name="Test Sport", sport_type=self.sport_type)

        self.tournament = Tournament.objects.create(
            id=uuid.uuid4(),
            name="Test Quiz Tournament",
            type=self.quiz_tournament_type,
            season=self.season,
            sport=self.sport
        )

        self.question_pool = QuestionPool.objects.create(id=uuid.uuid4(), name="General Knowledge", description="A pool of general knowledge questions")

        self.question1 = Question.objects.create(text="What is 2+2?", options=['3', '4', '5'], correct_answer='4', pool=self.question_pool)
        self.question2 = Question.objects.create(text="What is the capital of France?", options=['London', 'Paris', 'Berlin'], correct_answer='Paris', pool=self.question_pool)

    @patch('features.utils.authentication.FirebaseAuthentication.authenticate')
    def test_create_question(self, mock_authenticate):
        with patch('features.utils.permissions.IsAdminRole.has_permission') as mock_permission:
            mock_permission.return_value = True
            mock_authenticate.return_value = (self.admin_user, {'user_id': self.admin_user.firebase_uid})
            url = reverse('question-list')
            data = {
                'text': 'What is the color of the sky?',
                'options': ['Blue', 'Green', 'Red'],
                'correct_answer': 'Blue'
            }
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, 201)
            self.assertEqual(Question.objects.count(), 3)

    @patch('features.utils.authentication.FirebaseAuthentication.authenticate')
    def test_start_quiz_round(self, mock_authenticate):
        with patch('features.utils.permissions.IsAdminRole.has_permission') as mock_permission:
            mock_authenticate.return_value = (self.admin_user, {'user_id': self.admin_user.firebase_uid})
            mock_permission.return_value = True
            now = datetime.now(tz=timezone.utc)
            payload = {
                'tournament_id': str(self.tournament.id),
                'duration': 2,
                "question_pool": str(self.question_pool.id),
                'start_time': now.isoformat(),
                'end_time': (now + timedelta(hours=2)).isoformat()
            }
            url = reverse('start-quiz-round', kwargs={'tournament_id': self.tournament.id})
            response = self.client.post(url, content_type='application/json', data=payload)
            self.assertEqual(response.status_code, 201)
            self.assertEqual(QuizRound.objects.count(), 1)

    @patch('features.utils.authentication.FirebaseAuthentication.authenticate')
    def test_get_active_quiz_round(self, mock_authenticate):
        mock_authenticate.return_value = (self.user, {'user_id': self.user.firebase_uid})
        self.client.credentials(HTTP_AUTHORIZATION='Bearer dummy_user_token')

        # Initially, no tournament registration
        url = reverse('active-quiz-round')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Register to the quiz tournament
        self.user.tournament_user.add(self.tournament)
        self.user.save()

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 0) # No active round yet

        # Start a round
        with patch('features.utils.permissions.IsAdminRole.has_permission') as mock_permission:
            mock_authenticate.return_value = (self.admin_user, {'user_id': self.admin_user.firebase_uid})
            mock_permission.return_value = True
            now = datetime.now(tz=timezone.utc)
            payload = {
                'tournament_id': str(self.tournament.id),
                'duration': 2,
                "question_pool": str(self.question_pool.id),
                'start_time': now.isoformat(),
                'end_time': (now + timedelta(hours=2)).isoformat()
            }
            start_url = reverse('start-quiz-round', kwargs={'tournament_id': self.tournament.id})
            self.client.post(start_url, content_type='application/json', data=payload)

        # Now, get the active round
        mock_authenticate.return_value = (self.user, {'user_id': self.user.firebase_uid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)

    @patch('features.utils.authentication.FirebaseAuthentication.authenticate')
    def test_get_question(self, mock_authenticate):
        # Start a round
        with patch('features.utils.permissions.IsAdminRole.has_permission') as mock_permission:
            mock_authenticate.return_value = (self.admin_user, {'user_id': self.admin_user.firebase_uid})
            mock_permission.return_value = True
            now = datetime.now(tz=timezone.utc)
            payload = {
                'tournament_id': str(self.tournament.id),
                'duration': 2,
                "question_pool": str(self.question_pool.id),
                'start_time': now.isoformat(),
                'end_time': (now + timedelta(hours=2)).isoformat()
            }
            start_url = reverse('start-quiz-round', kwargs={'tournament_id': self.tournament.id})
            self.client.post(start_url, content_type='application/json', data=payload)

        mock_authenticate.return_value = (self.user, {'user_id': self.user.firebase_uid})
        url = reverse('get-question')
        
        # Get first question
        payload = {
            "quiz_round_id": str(QuizRound.objects.first().id)
        }
        response1 = self.client.post(url, content_type='application/json', data=payload)
        self.assertEqual(response1.status_code, 200)
        question1_id = response1.data['data'][0]['id']

        # Create a dummy attempt for the first question
        quiz_round = QuizRound.objects.first()
        question1 = Question.objects.get(id=question1_id)
        UserQuizAttempt.objects.create(user=self.user, quiz_round=quiz_round, question=question1, selected_answer="dummy")

        # Get second question
        response2 = self.client.post(url, content_type='application/json', data=payload)
        self.assertEqual(response2.status_code, 200)
        question2_id = response2.data['data'][0]['id']
        self.assertNotEqual(question1_id, question2_id)
        
        # Create a dummy attempt for the second question
        question2 = Question.objects.get(id=question2_id)
        UserQuizAttempt.objects.create(user=self.user, quiz_round=quiz_round, question=question2, selected_answer="dummy")

        # No more questions
        response3 = self.client.post(url, content_type='application/json', data=payload)
        self.assertEqual(response3.status_code, 404)

    @patch('features.utils.authentication.FirebaseAuthentication.authenticate')
    def test_submit_answer(self, mock_authenticate):
        with patch('features.utils.permissions.IsAdminRole.has_permission') as mock_permission:
            # Start a round
            mock_authenticate.return_value = (self.admin_user, {'user_id': self.admin_user.firebase_uid})
            mock_permission.return_value = True
            now = datetime.now(tz=timezone.utc)
            payload = {
                'tournament_id': str(self.tournament.id),
                'duration': 2,
                "question_pool": str(self.question_pool.id),
                'start_time': now.isoformat(),
                'end_time': (now + timedelta(hours=2)).isoformat()
            }
            start_url = reverse('start-quiz-round', kwargs={'tournament_id': self.tournament.id})
            self.client.post(start_url, content_type='application/json', data=payload)

        mock_authenticate.return_value = (self.user, {'user_id': self.user.firebase_uid})
        
        # Get a question
        payload = {
            "quiz_round_id": str(QuizRound.objects.first().id)
        }
        get_question_url = reverse('get-question')
        response = self.client.post(get_question_url, content_type='application/json', data=payload)
        question_id = response.data['data'][0]['id']
        question = Question.objects.get(id=question_id)
        
        # Submit a correct answer
        submit_url = reverse('submit-answer')
        data = {'question': question.pk, 'selected_answer': question.correct_answer, 'quiz_round': str(QuizRound.objects.first().id)}
        response = self.client.post(submit_url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['data']['correct'])
        self.assertEqual(response.data['data']['score'], 1)

        # Try to submit again
        response = self.client.post(submit_url, data, format='json')
        self.assertEqual(response.status_code, 400)

        # Get another question
        response = self.client.post(get_question_url, content_type='application/json', data=payload)
        question_id = response.data['data'][0]['id']
        question = Question.objects.get(id=question_id)
        
        # Submit an incorrect answer
        data = {'question': question.pk, 'selected_answer': 'wrong_answer', 'quiz_round': str(QuizRound.objects.first().id)}
        response = self.client.post(submit_url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['data']['correct'])
        self.assertEqual(response.data['data']['score'], 1) # Score should still be 1 from the previous correct answer

    # @patch('features.utils.authentication.FirebaseAuthentication.authenticate')
    # @patch('features.utils.permissions.IsAdminRole.has_permission')
    # def test_get_leaderboard(self, mock_authenticate, mock_permission):
    #     # Start a round
    #     mock_authenticate.return_value = (self.admin_user, {'user_id': self.admin_user.firebase_uid})
    #     mock_permission.return_value = True
    #     start_url = reverse('start-quiz-round')
    #     self.client.post(start_url)
    #     quiz_round = QuizRound.objects.first()

    #     # User 1 submits a correct answer
    #     mock_authenticate.return_value = (self.user, {'user_id': self.user.firebase_uid})
    #     submit_url = reverse('submit-answer')
    #     data = {'question': self.question1.pk, 'selected_answer': self.question1.correct_answer}
    #     self.client.post(submit_url, data, format='json')

    #     # User 2 submits two correct answers
    #     user2 = User.objects.create(firebase_uid="test_user_2_uid", username="test_user_2", role=['USER'])
    #     mock_authenticate.return_value = (user2, {'user_id': user2.firebase_uid})
    #     data = {'question': self.question1.pk, 'selected_answer': self.question1.correct_answer}
    #     self.client.post(submit_url, data, format='json')
    #     data = {'question': self.question2.pk, 'selected_answer': self.question2.correct_answer}
    #     self.client.post(submit_url, data, format='json')

    #     # Get leaderboard
    #     mock_authenticate.return_value = (self.user, {'user_id': self.user.firebase_uid})
    #     url = reverse('quiz-leaderboard', kwargs={'quiz_round_id': quiz_round.id})
    #     response = self.client.get(url)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(len(response.data), 2)
    #     self.assertEqual(response.data[0]['user_name'], user2.username)
    #     self.assertEqual(response.data[0]['score'], 2)
    #     self.assertEqual(response.data[1]['user_name'], self.user.username)
    #     self.assertEqual(response.data[1]['score'], 1)