from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from features.users.models import User
from features.metric.models import StepMetric

from unittest.mock import patch
from datetime import datetime, timezone, timedelta
from rest_framework import status

# Create your tests here.
class UploadStepMetricTest(APITestCase):
    def setUp(self):

        # Create user
        self.user = User.objects.create(firebase_uid="123", username="123")
        self.date = datetime.now(timezone.utc).isoformat()


    
    @patch('features.utils.authentication.FirebaseAuthentication.authenticate')
    def test_upload_steps_count(self, mock_authenticate):
        """
        Test update for the first time. Either its a new user or the data is for new day
        """
        current_user = self.user
        fake_auth_payload = {
            'user_id': str(current_user.pk)
        }
        mock_authenticate.return_value = (current_user, fake_auth_payload)

        url = reverse('step-metric')
        count = 700
        payload = {
            'date': self.date,
            'count': count
        }
        response = self.client.post(url, data=payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        step_metric = StepMetric.objects.get(user=self.user)
        self.assertEqual(step_metric.count, count)
    
    @patch('features.utils.authentication.FirebaseAuthentication.authenticate')
    def test_upload_steps_count(self, mock_authenticate):
        """
        Test update for the same day
        """
        current_user = self.user
        fake_auth_payload = {
            'user_id': str(current_user.pk)
        }
        mock_authenticate.return_value = (current_user, fake_auth_payload)

        url = reverse('step-metric')
        count = 1000
        payload = {
            'date': self.date,
            'count': count
        }
        response = self.client.post(url, data=payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        step_metric = StepMetric.objects.get(user=self.user)
        self.assertEqual(step_metric.count, count)
    
    @patch('features.utils.authentication.FirebaseAuthentication.authenticate')
    def test_upload_steps_count(self, mock_authenticate):
        """
        Test update for second day
        """
        current_user = self.user
        fake_auth_payload = {
            'user_id': str(current_user.pk)
        }
        mock_authenticate.return_value = (current_user, fake_auth_payload)

        url = reverse('step-metric')
        count_one = 1000
        payload = {
            'date': self.date,
            'count': count_one
        }
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        count_two = 500
        payload['date'] = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        payload['count'] = count_two
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        row_count = StepMetric.objects.filter(user=self.user).count()
        self.assertEqual(row_count, 2)