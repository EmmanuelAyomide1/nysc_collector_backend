from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory, APITestCase

from apps.common.permissions import IsAdministrator, IsMember

User = get_user_model()


class RolePermissionTests(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.member = User.objects.create_user(
            email="member@example.com",
            password="x",
            batch="A1",
            code_no=1,
            first_name="M",
            last_name="M",
        )
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="x",
            batch="A1",
            code_no=2,
            first_name="A",
            last_name="A",
            role=User.Role.ADMIN,
        )

    def test_is_member_allows_member(self):
        request = self.factory.get("/")
        request.user = self.member

        self.assertTrue(IsMember().has_permission(request, None))

    def test_is_member_denies_admin(self):
        request = self.factory.get("/")
        request.user = self.admin

        self.assertFalse(IsMember().has_permission(request, None))

    def test_is_administrator_allows_admin(self):
        request = self.factory.get("/")
        request.user = self.admin

        self.assertTrue(IsAdministrator().has_permission(request, None))

    def test_is_administrator_denies_member(self):
        request = self.factory.get("/")
        request.user = self.member

        self.assertFalse(IsAdministrator().has_permission(request, None))

    def test_permissions_deny_anonymous(self):
        request = self.factory.get("/")
        request.user = AnonymousUser()

        self.assertFalse(IsMember().has_permission(request, None))
        self.assertFalse(IsAdministrator().has_permission(request, None))


class ExceptionHandlerTests(APITestCase):
    def test_validation_error_wrapped_in_envelope(self):
        response = self.client.post("/api/auth/register/", {}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["success"])
        self.assertIn("message", response.data)

    def test_authentication_error_wrapped_in_envelope(self):
        response = self.client.get("/api/users/me/")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.data,
            {
                "success": False,
                "message": "Authentication credentials were not provided.",
            },
        )
