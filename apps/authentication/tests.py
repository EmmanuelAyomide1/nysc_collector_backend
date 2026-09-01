from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.authentication import CookieJWTAuthentication
from apps.authentication.models import Otp
from apps.common.constants import ACCESS_TOKEN_COOKIE_NAME, REFRESH_TOKEN_COOKIE_NAME
from apps.members.models import Batch

User = get_user_model()


def make_user(email="corper@example.com", **overrides):
    batch_name = overrides.pop("batch", "A1")
    batch, _ = Batch.objects.get_or_create(year=2099, name=batch_name)

    fields = {
        "password": "S0me-Str0ng-Pass!",
        "batch": batch,
        "code_no": 1234,
        "first_name": "Ada",
        "last_name": "Okafor",
    }
    fields.update(overrides)
    return User.objects.create_user(email=email, **fields)


class RegisterViewTests(APITestCase):
    url = "/api/auth/register/"

    def setUp(self):
        self.batch = Batch.objects.create(year=2099, name="A1", is_active=True)

    def valid_payload(self, **overrides):
        payload = {
            "email": "corper@example.com",
            "password": "S0me-Str0ng-Pass!",
            "batch": str(self.batch.id),
            "code_no": 1234,
            "first_name": "Ada",
            "last_name": "Okafor",
            "phone_number": "0812345678",
        }
        payload.update(overrides)
        return payload

    def test_register_success(self):
        response = self.client.post(self.url, self.valid_payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["email"], "corper@example.com")
        self.assertNotIn("password", response.data["data"])

        user = User.objects.get(email="corper@example.com")
        self.assertTrue(user.check_password("S0me-Str0ng-Pass!"))
        self.assertEqual(user.role, User.Role.MEMBER)

    def test_register_duplicate_email_rejected(self):
        make_user(email="corper@example.com", batch="A2", code_no=9999)

        response = self.client.post(self.url, self.valid_payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    def test_register_duplicate_batch_code_no_rejected(self):
        make_user(email="other@example.com", batch="A1", code_no=1234)

        response = self.client.post(self.url, self.valid_payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_weak_password_rejected(self):
        response = self.client.post(
            self.url, self.valid_payload(password="123"), format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_invalid_phone_number_rejected(self):
        response = self.client.post(
            self.url, self.valid_payload(phone_number="123"), format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_required_field_rejected(self):
        payload = self.valid_payload()
        del payload["batch"]

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_role_cannot_be_set_by_client(self):
        response = self.client.post(
            self.url, self.valid_payload(role="admin"), format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="corper@example.com")
        self.assertEqual(user.role, User.Role.MEMBER)


class LoginViewTests(APITestCase):
    url = "/api/auth/login/"

    def setUp(self):
        self.user = make_user()

    def test_login_success_sets_cookies(self):
        response = self.client.post(
            self.url,
            {"email": "corper@example.com", "password": "S0me-Str0ng-Pass!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn(ACCESS_TOKEN_COOKIE_NAME, response.cookies)
        self.assertIn(REFRESH_TOKEN_COOKIE_NAME, response.cookies)
        self.assertTrue(response.cookies[ACCESS_TOKEN_COOKIE_NAME]["httponly"])
        self.assertTrue(response.cookies[REFRESH_TOKEN_COOKIE_NAME]["httponly"])

    def test_login_wrong_password_rejected(self):
        response = self.client.post(
            self.url,
            {"email": "corper@example.com", "password": "wrong-password"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    def test_login_unknown_email_rejected(self):
        response = self.client.post(
            self.url,
            {"email": "nobody@example.com", "password": "whatever"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_inactive_user_rejected(self):
        self.user.is_active = False
        self.user.save()

        response = self.client.post(
            self.url,
            {"email": "corper@example.com", "password": "S0me-Str0ng-Pass!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LogoutViewTests(APITestCase):
    def setUp(self):
        self.user = make_user()
        login = self.client.post(
            "/api/auth/login/",
            {"email": "corper@example.com", "password": "S0me-Str0ng-Pass!"},
            format="json",
        )
        self.refresh_token = login.cookies[REFRESH_TOKEN_COOKIE_NAME].value

    def test_logout_clears_cookies(self):
        response = self.client.post("/api/auth/logout/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.cookies[ACCESS_TOKEN_COOKIE_NAME].value, "")
        self.assertEqual(response.cookies[REFRESH_TOKEN_COOKIE_NAME].value, "")

    def test_logout_blacklists_refresh_token(self):
        self.client.post("/api/auth/logout/")

        self.client.cookies[REFRESH_TOKEN_COOKIE_NAME] = self.refresh_token
        response = self.client.post("/api/auth/refresh/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_without_session_still_succeeds(self):
        self.client.cookies.clear()

        response = self.client.post("/api/auth/logout/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class RefreshViewTests(APITestCase):
    def setUp(self):
        self.user = make_user()
        login = self.client.post(
            "/api/auth/login/",
            {"email": "corper@example.com", "password": "S0me-Str0ng-Pass!"},
            format="json",
        )
        self.original_refresh = login.cookies[REFRESH_TOKEN_COOKIE_NAME].value

    def test_refresh_rotates_tokens(self):
        response = self.client.post("/api/auth/refresh/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_refresh = response.cookies[REFRESH_TOKEN_COOKIE_NAME].value
        self.assertNotEqual(new_refresh, self.original_refresh)

    def test_reusing_rotated_refresh_token_fails_cleanly(self):
        self.client.post("/api/auth/refresh/")  # rotates; original now blacklisted

        self.client.cookies[REFRESH_TOKEN_COOKIE_NAME] = self.original_refresh
        response = self.client.post("/api/auth/refresh/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data["success"])

    def test_refresh_without_cookie_rejected(self):
        self.client.cookies.clear()

        response = self.client.post("/api/auth/refresh/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CookieJWTAuthenticationTests(APITestCase):
    def setUp(self):
        self.user = make_user()
        self.factory = APIRequestFactory()
        self.auth = CookieJWTAuthentication()

    def test_authenticates_with_valid_cookie(self):
        access_token = str(RefreshToken.for_user(self.user).access_token)
        request = self.factory.get(
            "/", HTTP_COOKIE=f"{ACCESS_TOKEN_COOKIE_NAME}={access_token}"
        )

        result = self.auth.authenticate(request)

        self.assertIsNotNone(result)
        self.assertEqual(result[0], self.user)

    def test_returns_none_without_cookie(self):
        request = self.factory.get("/")

        self.assertIsNone(self.auth.authenticate(request))

    def test_raises_on_invalid_token(self):
        request = self.factory.get(
            "/", HTTP_COOKIE=f"{ACCESS_TOKEN_COOKIE_NAME}=garbage"
        )

        with self.assertRaises(InvalidToken):
            self.auth.authenticate(request)


class ForgotPasswordViewTests(APITestCase):
    url = "/api/auth/forgot-password/"

    def test_known_email_creates_otp(self):
        user = make_user()

        response = self.client.post(self.url, {"email": user.email}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertTrue(Otp.objects.filter(user=user, is_used=False).exists())

    def test_unknown_email_still_succeeds_without_creating_otp(self):
        response = self.client.post(
            self.url, {"email": "nobody@example.com"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertFalse(Otp.objects.exists())

    def test_repeat_request_invalidates_previous_otp(self):
        user = make_user()

        self.client.post(self.url, {"email": user.email}, format="json")
        self.client.post(self.url, {"email": user.email}, format="json")

        self.assertEqual(Otp.objects.filter(user=user).count(), 2)
        self.assertEqual(Otp.objects.filter(user=user, is_used=False).count(), 1)

    def test_invalid_email_rejected(self):
        response = self.client.post(self.url, {"email": "not-an-email"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmViewTests(APITestCase):
    url = "/api/auth/reset-password/"

    def setUp(self):
        self.user = make_user()
        self.otp = Otp.generate_otp(self.user, expiry_minutes=60)

    def valid_payload(self, **overrides):
        payload = {
            "otp": self.otp.otp,
            "password": "N3w-Str0ng-Pass!",
            "confirm_password": "N3w-Str0ng-Pass!",
        }
        payload.update(overrides)
        return payload

    def test_valid_otp_resets_password(self):
        response = self.client.post(self.url, self.valid_payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("N3w-Str0ng-Pass!"))
        self.otp.refresh_from_db()
        self.assertTrue(self.otp.is_used)

    def test_otp_is_single_use(self):
        self.client.post(self.url, self.valid_payload(), format="json")

        response = self.client.post(
            self.url,
            self.valid_payload(password="An0ther-Str0ng-Pass!",
                                confirm_password="An0ther-Str0ng-Pass!"),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mismatched_confirmation_rejected(self):
        response = self.client.post(
            self.url,
            self.valid_payload(confirm_password="Different-Pass!1"),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password("Different-Pass!1"))

    def test_unknown_otp_rejected(self):
        response = self.client.post(
            self.url, self.valid_payload(otp="does-not-exist"), format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_expired_otp_rejected(self):
        self.otp.expires_at = timezone.now() - timezone.timedelta(minutes=1)
        self.otp.save(update_fields=["expires_at"])

        response = self.client.post(self.url, self.valid_payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_weak_password_rejected(self):
        response = self.client.post(
            self.url,
            self.valid_payload(password="123", confirm_password="123"),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestListViewTests(APITestCase):
    url = "/api/auth/password-reset-requests/"

    def setUp(self):
        self.admin = make_user(
            email="admin@example.com", role=User.Role.ADMIN, code_no=1
        )
        self.member = make_user(email="member@example.com", code_no=2)
        self.otp = Otp.generate_otp(self.member, expiry_minutes=60)

    def login(self, email, password="S0me-Str0ng-Pass!"):
        self.client.post(
            "/api/auth/login/", {"email": email, "password": password}, format="json"
        )

    def test_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_member_cannot_list(self):
        self.login(self.member.email)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_list(self):
        self.login(self.admin.email)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["data"]["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["otp"], self.otp.otp)
        self.assertEqual(results[0]["user"]["email"], self.member.email)
