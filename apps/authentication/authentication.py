from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.common.constants import ACCESS_TOKEN_COOKIE_NAME


class CookieJWTAuthentication(JWTAuthentication):
    """Reads the JWT access token from an HttpOnly cookie instead of the
    Authorization header, per nysc_collector_backend/PLAN.md's cookie-based
    JWT authentication requirement.
    """

    def authenticate(self, request):
        raw_token = request.COOKIES.get(ACCESS_TOKEN_COOKIE_NAME)
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token
