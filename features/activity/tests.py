from django.test import TestCase
from rest_framework.test import APITestCase
from unittest.mock import patch
from django.urls import reverse
import logging
import json

from features.users.models import User
from features.metric.models import MetricConfig
from features.activity.models import ActivityData, ActivityConfig, ActivityMetric

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
                },
                {
                    "id": self.metric_config_2.id,
                    "value": 200
                }
            ],
            "start_datetime": "2023-10-01T12:00:00Z",
            "end_datetime": "2023-10-01T13:00:00Z"
        }

        url = reverse('activity-data-post')
        response = self.client.post(url, content_type='application/json', data=payload)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(ActivityData.objects.count(), 1)
        activity_data = ActivityData.objects.first()
        self.assertEqual(activity_data.activity, self.activity)
        self.assertEqual(activity_data.user, current_user)
        self.assertEqual(activity_data.start_date.isoformat(), "2023-10-01")
        self.assertEqual(activity_data.end_date.isoformat(), "2023-10-01")

        metrics = ActivityMetric.objects.filter(activity_data=activity_data)
        self.assertEqual(metrics.count(), 2)
        metric1 = metrics.get(metric=self.metric_config)
        self.assertEqual(metric1.value, 100)
        metric2 = metrics.get(metric=self.metric_config_2)
        self.assertEqual(metric2.value, 200)
    
    def test_activity_data_upload_data_not_aggregated(self):
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

        current_user = self.user
        fake_auth_payload = {
            'user_id': str(current_user.pk)
        }

        with patch('features.utils.authentication.FirebaseAuthentication.authenticate', return_value=(current_user, fake_auth_payload)):
            url = reverse('activity-data-post')
            response1 = self.client.post(url, content_type='application/json', data=payload)
            response2 = self.client.post(url, content_type='application/json', data=payload)
            self.assertEqual(response1.status_code, 201)
            self.assertEqual(response2.status_code, 201)
            self.assertEqual(ActivityData.objects.count(), 1)

            activity_data = ActivityData.objects.first()
            self.assertEqual(activity_data.activity, self.activity)
            self.assertEqual(activity_data.user, current_user)
            self.assertEqual(activity_data.start_date.isoformat(), "2023-10-01")
            self.assertEqual(activity_data.end_date.isoformat(), "2023-10-01")

            metrics = ActivityMetric.objects.filter(activity_data=activity_data)
            self.assertEqual(metrics.count(), 1)
            metric = metrics.get(metric=self.metric_config)
            self.assertEqual(metric.value, 100)
    
    def test_activity_data_upload_multiple_days(self):
        payload_day1 = {
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

        payload_day2 = {
            "user": self.user.pk,
            "activity": self.activity.id,
            "metrics": [
                {
                    "id": self.metric_config.id,
                    "value": 200
                }
            ],
            "start_datetime": "2023-10-02T12:00:00Z",
            "end_datetime": "2023-10-02T13:00:00Z"
        }

        current_user = self.user
        fake_auth_payload = {
            'user_id': str(current_user.pk)
        }

        with patch('features.utils.authentication.FirebaseAuthentication.authenticate', return_value=(current_user, fake_auth_payload)):
            url = reverse('activity-data-post')
            response1 = self.client.post(url, content_type='application/json', data=payload_day1)
            response2 = self.client.post(url, content_type='application/json', data=payload_day2)
            self.assertEqual(response1.status_code, 201)
            self.assertEqual(response2.status_code, 201)
            self.assertEqual(ActivityData.objects.count(), 2)

            activity_data_day1 = ActivityData.objects.get(start_date="2023-10-01")
            self.assertEqual(activity_data_day1.activity, self.activity)
            self.assertEqual(activity_data_day1.user, current_user)
            self.assertEqual(activity_data_day1.start_date.isoformat(), "2023-10-01")
            self.assertEqual(activity_data_day1.end_date.isoformat(), "2023-10-01")

            metrics_day1 = ActivityMetric.objects.filter(activity_data=activity_data_day1)
            self.assertEqual(metrics_day1.count(), 1)
            metric1 = metrics_day1.get(metric=self.metric_config)
            self.assertEqual(metric1.value, 100)

            activity_data_day2 = ActivityData.objects.get(start_date="2023-10-02")
            self.assertEqual(activity_data_day2.activity, self.activity)
            self.assertEqual(activity_data_day2.user, current_user)
            self.assertEqual(activity_data_day2.start_date.isoformat(), "2023-10-02")
            self.assertEqual(activity_data_day2.end_date.isoformat(), "2023-10-02")
            metrics_day2 = ActivityMetric.objects.filter(activity_data=activity_data_day2)
            self.assertEqual(metrics_day2.count(), 1)
            metric2 = metrics_day2.get(metric=self.metric_config)
            self.assertEqual(metric2.value, 200)