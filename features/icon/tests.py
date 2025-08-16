import uuid
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile

from features.users.models import User
from features.icon.models import Icon

@override_settings(
    AWS_REGION='us-east-1',
    AWS_ACCESS_KEY_ID='test',
    AWS_SECRET_ACCESS_KEY='test',
    AWS_STORAGE_BUCKET_NAME='test-bucket'
)
class IconAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create(firebase_uid=f"admin_{uuid.uuid4()}", email="admin@example.com", role=["ADMIN"])

    def _get_mock_auth_path(self):
        return 'features.utils.authentication.FirebaseAuthentication.authenticate'

    @patch('requests.put')
    def test_create_icon_upload(self, mock_put):
        """
        Ensure admin users can create a new icon by uploading a file.
        """
        # Mock the S3 upload
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_put.return_value = mock_response

        # Create a dummy file
        dummy_file = SimpleUploadedFile("test_icon.png", b"file_content", content_type="image/png")

        with patch(self._get_mock_auth_path()) as mock_auth:
            mock_auth.return_value = (self.admin_user, {'roles': ['ADMIN'], 'uid': self.admin_user.firebase_uid})
            url = reverse('icon-list')
            data = {'file': dummy_file, 'name': 'Test Icon'}
            response = self.client.post(url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Icon.objects.count(), 1)
        icon = Icon.objects.first()
        self.assertEqual(icon.name, 'Test Icon')
        self.assertTrue(icon.url.endswith('test_icon.png'))
        mock_put.assert_called_once()
