from django.conf import settings
from rest_framework import serializers

from apps.common.constants import ACCESS_TOKEN_COOKIE_NAME, REFRESH_TOKEN_COOKIE_NAME


def validate_phone_number(value):
    """
    Validate the phone number format.
    """
    if not value.isdigit() or len(value) != 10:
        raise serializers.ValidationError("Phone number must be 10 digits long.")
    return value


def set_auth_cookies(response, access_token, refresh_token=None):
    response.set_cookie(
        ACCESS_TOKEN_COOKIE_NAME,
        access_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="None",
    )
    if refresh_token is not None:
        response.set_cookie(
            REFRESH_TOKEN_COOKIE_NAME,
            refresh_token,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="None",
        )
    return response
