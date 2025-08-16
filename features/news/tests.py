from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch
import uuid

from features.users.models import User
from features.news.models import News
from features.icon.models import Icon

class NewsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create(firebase_uid=f"admin_{uuid.uuid4()}", email="admin@example.com", role=["ADMIN"])
        self.regular_user = User.objects.create(firebase_uid=f"user_{uuid.uuid4()}", email="user@example.com", role=["USER"])
        self.icon = Icon.objects.create(name="Test Icon", url="http://example.com/icon.png")

        self.news_data = {
            "title": "Test News",
            "description": "This is a test news.",
            "is_carousel": False,
            "icon_id": self.icon.id,
        }

    def _get_mock_auth_path(self, role):
        return 'features.utils.authentication.FirebaseAuthentication.authenticate'

    def test_add_news_admin(self):
        """
        Ensure admin users can create a new news item.
        """
        with patch(self._get_mock_auth_path("ADMIN")) as mock_auth:
            mock_auth.return_value = (self.admin_user, {'roles': ['ADMIN'], 'uid': self.admin_user.firebase_uid})
            url = reverse('add-news')
            response = self.client.post(url, self.news_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(News.objects.count(), 1)
            self.assertEqual(News.objects.get().title, "Test News")

    def test_add_news_non_admin(self):
        """
        Ensure non-admin users cannot create a new news item.
        """
        with patch(self._get_mock_auth_path("USER")) as mock_auth:
            mock_auth.return_value = (self.regular_user, {'roles': ['USER'], 'uid': self.regular_user.firebase_uid})
            url = reverse('add-news')
            response = self.client.post(url, self.news_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_news(self):
        """
        Ensure users can list news items, with carousel news excluded.
        """
        # Create some news
        News.objects.create(title="Normal News 1", description="...", is_carousel=False)
        c1 = News.objects.create(title="Carousel News 1", description="...", is_carousel=True)
        c2 = News.objects.create(title="Carousel News 2", description="...", is_carousel=True)
        c3 = News.objects.create(title="Carousel News 3", description="...", is_carousel=True)
        c4 = News.objects.create(title="Carousel News 4", description="...", is_carousel=True) # Should be in list

        with patch(self._get_mock_auth_path("USER")) as mock_auth:
            mock_auth.return_value = (self.regular_user, {'roles': ['USER'], 'uid': self.regular_user.firebase_uid})
            url = reverse('list-news')
            response = self.client.get(url, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data['results']), 2) # Normal News 1 and Carousel News 1
            titles = [item['title'] for item in response.data['results']]
            self.assertIn("Normal News 1", titles)
            self.assertIn("Carousel News 1", titles)
            self.assertNotIn("Carousel News 2", titles)
            self.assertNotIn("Carousel News 3", titles)
            self.assertNotIn("Carousel News 4", titles)

    def test_list_carousel(self):
        """
        Ensure the carousel endpoint returns the top 3 carousel news.
        """
        # Create some news
        News.objects.create(title="Normal News 1", description="...", is_carousel=False)
        c1 = News.objects.create(title="Carousel News 1", description="...", is_carousel=True)
        c2 = News.objects.create(title="Carousel News 2", description="...", is_carousel=True)
        c3 = News.objects.create(title="Carousel News 3", description="...", is_carousel=True)
        c4 = News.objects.create(title="Carousel News 4", description="...", is_carousel=True)

        with patch(self._get_mock_auth_path("USER")) as mock_auth:
            mock_auth.return_value = (self.regular_user, {'roles': ['USER'], 'uid': self.regular_user.firebase_uid})
            url = reverse('list-carousel')
            response = self.client.get(url, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data['data']), 3)
            titles = [item['title'] for item in response.data['data']]
            self.assertIn("Carousel News 2", titles)
            self.assertIn("Carousel News 3", titles)
            self.assertIn("Carousel News 4", titles)
            self.assertNotIn("Carousel News 1", titles)

    def test_update_news_admin(self):
        """
        Ensure admin users can update a news item.
        """
        news = News.objects.create(**self.news_data)
        with patch(self._get_mock_auth_path("ADMIN")) as mock_auth:
            mock_auth.return_value = (self.admin_user, {'roles': ['ADMIN'], 'uid': self.admin_user.firebase_uid})
            url = reverse('index-operations', kwargs={'id': news.id})
            updated_data = {'title': 'Updated Title'}
            response = self.client.put(url, updated_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            news.refresh_from_db()
            self.assertEqual(news.title, 'Updated Title')

    def test_delete_news_admin(self):
        """
        Ensure admin users can delete a news item.
        """
        news = News.objects.create(**self.news_data)
        with patch(self._get_mock_auth_path("ADMIN")) as mock_auth:
            mock_auth.return_value = (self.admin_user, {'roles': ['ADMIN'], 'uid': self.admin_user.firebase_uid})
            url = reverse('index-operations', kwargs={'id': news.id})
            response = self.client.delete(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(News.objects.count(), 0)
