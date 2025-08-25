from django.test import TestCase
from rest_framework.test import APITestCase
from unittest.mock import patch
from django.urls import reverse
import logging

from features.users.models import User
from features.metric.models import MetricConfig
from features.activity.models import ActivityData, ActivityConfig

logger = logging.getLogger(__name__)

# Create your tests here.
class ActivityDataTest(APITestCase):
    def setUp(self):
        
        # Insert User
        self.user = User.objects.create(firebase_uid="123", username="123")

        # Insert MetricConfig
        self.metric_config = MetricConfig.objects.create(
            metric_type="Test Metric",
            description="Test Description"
        )

        # Insert Activity
        self.activity = ActivityConfig.objects.create(
            activity_type="Test Activity",
            description="Test Activity Description",
        )
        self.activity.metrics.add(self.metric_config)
    
    @patch('features.utils.authentication.FirebaseAuthentication.authenticate')
    def test_activity_data_upload(self, mock_authenticate):
        current_user = self.user

        fake_auth_payload = {
            'user_id': str(current_user.pk)
        }

        mock_authenticate.return_value = (current_user, fake_auth_payload)
        
        payload = {
            "user": self.user.pk,
            "activity": self.activity.id,
            "metrics": [
                {
                    "id": self.metric_config.id,
                    "value": 100
                }
            ],
            "start_datetime": "2023-10-01T12:00:00Z",
            "end_datetime": "2023-10-01T13:00:00Z"
        }

        url = reverse('activity-data-upload')
        response = self.client.post(url, data=payload)
        logger.info(response.data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ActivityData.objects.count(), 1)
        activity_data = ActivityData.objects.first()
        self.assertEqual(activity_data.activity, self.activity)
        self.assertEqual(activity_data.user, current_user)
        self.assertEqual(activity_data.start_datetime.isoformat(), "2023-10-01T12:00:00+00:00")
        self.assertEqual(activity_data.end_datetime.isoformat(), "2023-10-01T13:00:00+00:00")
        self.assertEqual(activity_data.metrics.count(), 1)
        metric_data = activity_data.metrics.first()
        self.assertEqual(metric_data.metric, self.metric_config)
        self.assertEqual(metric_data.value, 100)