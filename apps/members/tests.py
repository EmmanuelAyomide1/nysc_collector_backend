from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class MemberTestsBase(APITestCase):
    def setUp(self):
        self.member = User.objects.create_user(
            email="member@example.com",
            password="S0me-Str0ng-Pass!",
            batch="A1",
            code_no=1,
            first_name="Ada",
            last_name="Okafor",
        )
        self.other_member = User.objects.create_user(
            email="other@example.com",
            password="S0me-Str0ng-Pass!",
            batch="A1",
            code_no=2,
            first_name="Bola",
            last_name="Ade",
        )
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="S0me-Str0ng-Pass!",
            batch="A1",
            code_no=3,
            first_name="Chidi",
            last_name="Eze",
            role=User.Role.ADMIN,
        )

    def login(self, email, password="S0me-Str0ng-Pass!"):
        self.client.post(
            "/api/auth/login/", {"email": email, "password": password}, format="json"
        )


class MemberListViewTests(MemberTestsBase):
    list_url = reverse("members:members-list")

    def test_admin_can_list_members(self):
        self.login(self.admin.email)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["count"], 3)

    def test_member_cannot_list_members(self):
        self.login(self.member.email)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_requires_authentication(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MemberDetailViewTests(MemberTestsBase):
    def url(self, member):
        return reverse("members:members-detail", kwargs={"pk": member.id})

    def test_member_can_view_own_profile(self):
        self.login(self.member.email)

        response = self.client.get(self.url(self.member))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["email"], self.member.email)

    def test_member_cannot_view_another_members_profile(self):
        self.login(self.member.email)

        response = self.client.get(self.url(self.other_member))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_view_any_members_profile(self):
        self.login(self.admin.email)

        response = self.client.get(self.url(self.member))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["email"], self.member.email)

    def test_admin_can_update_member_profile(self):
        self.login(self.admin.email)

        response = self.client.patch(
            self.url(self.member), {"first_name": "Updated"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["first_name"], "Updated")
        self.member.refresh_from_db()
        self.assertEqual(self.member.first_name, "Updated")

    def test_member_cannot_update_own_profile(self):
        self.login(self.member.email)

        response = self.client.patch(
            self.url(self.member), {"first_name": "Updated"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class MemberActivateDeactivateViewTests(MemberTestsBase):
    def test_admin_can_deactivate_member(self):
        self.login(self.admin.email)

        response = self.client.post(
            reverse("members:members-deactivate-member", kwargs={"pk": self.member.id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["data"]["is_active"])
        self.member.refresh_from_db()
        self.assertFalse(self.member.is_active)

    def test_admin_can_activate_member(self):
        self.member.is_active = False
        self.member.save(update_fields=["is_active"])
        self.login(self.admin.email)

        response = self.client.post(
            reverse("members:members-activate-member", kwargs={"pk": self.member.id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["data"]["is_active"])
        self.member.refresh_from_db()
        self.assertTrue(self.member.is_active)

    def test_member_cannot_activate_or_deactivate(self):
        self.login(self.member.email)

        response = self.client.post(
            reverse(
                "members:members-deactivate-member", kwargs={"pk": self.other_member.id}
            )
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
