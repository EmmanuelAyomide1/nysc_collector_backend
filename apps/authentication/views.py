from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator

from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.models import Otp
from apps.authentication.serializers import (
    ForgotPasswordRequestSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
)
from apps.users.serializers import UserSerializer
from apps.authentication.utils import set_auth_cookies
from apps.common.constants import ACCESS_TOKEN_COOKIE_NAME, REFRESH_TOKEN_COOKIE_NAME
from apps.common.permissions import IsAdministrator

# The admin resolves reset requests manually over WhatsApp, so the code needs
# to stay valid well past a typical short-lived OTP window.
PASSWORD_RESET_OTP_EXPIRY_MINUTES = 60 * 24


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        request_body=RegisterSerializer, tags=["Authentication"]
    ),
)
class RegisterView(APIView):
    permission_classes = [AllowAny]

    serializer_class = RegisterSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {"success": True, "data": self.serializer_class(user).data},
            status=status.HTTP_201_CREATED,
        )


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        request_body=LoginSerializer, tags=["Authentication"]
    ),
)
class LoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)

        response = Response(
            {"success": True, "data": UserSerializer(user).data},
            status=status.HTTP_200_OK,
        )
        return set_auth_cookies(response, str(refresh.access_token), str(refresh))


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(tags=["Authentication"]),
)
class LogoutView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get(REFRESH_TOKEN_COOKIE_NAME)
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except TokenError:
                pass

        response = Response({"success": True, "data": {}}, status=status.HTTP_200_OK)
        response.delete_cookie(ACCESS_TOKEN_COOKIE_NAME)
        response.delete_cookie(REFRESH_TOKEN_COOKIE_NAME)
        return response


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(tags=["Authentication"]),
)
class RefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get(REFRESH_TOKEN_COOKIE_NAME)
        if refresh_token is None:
            raise InvalidToken("No refresh token cookie provided.")

        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as exc:
            raise InvalidToken(str(exc))

        response = Response({"success": True, "data": {}}, status=status.HTTP_200_OK)
        return set_auth_cookies(
            response,
            serializer.validated_data["access"],
            serializer.validated_data.get("refresh"),
        )


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        request_body=ForgotPasswordRequestSerializer, tags=["Authentication"]
    ),
)
class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    serializer_class = ForgotPasswordRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = (
            get_user_model()
            .objects.filter(email__iexact=serializer.validated_data["email"])
            .first()
        )
        if user is not None:
            Otp.generate_otp(user, expiry_minutes=PASSWORD_RESET_OTP_EXPIRY_MINUTES)

        # Always respond the same way regardless of whether the email is
        # registered, so the response can't be used to enumerate accounts.
        return Response({"success": True, "data": {}}, status=status.HTTP_200_OK)


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        request_body=PasswordResetConfirmSerializer, tags=["Authentication"]
    ),
)
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"success": True, "data": {}}, status=status.HTTP_200_OK)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(tags=["Authentication"]),
)
class PasswordResetRequestListView(generics.ListAPIView):
    queryset = Otp.objects.select_related("user").order_by("-created_at")
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [IsAdministrator]
