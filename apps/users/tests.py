from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.members.models import Batch

User = get_user_model()


class CurrentUserViewTests(APITestCase):
    url = "/api/users/me/"

    def setUp(self):
        self.batch, _ = Batch.objects.get_or_create(year=2026, name="A1")
        self.user = User.objects.create_user(
            email="corper@example.com",
            password="S0me-Str0ng-Pass!",
            batch=self.batch,
            code_no=1234,
            first_name="Ada",
            last_name="Okafor",
        )

    def test_returns_authenticated_users_profile(self):
        self.client.post(
            "/api/auth/login/",
            {"email": "corper@example.com", "password": "S0me-Str0ng-Pass!"},
            format="json",
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["email"], "corper@example.com")
        self.assertEqual(response.data["data"]["role"], "member")
        self.assertNotIn("password", response.data["data"])

    def test_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
