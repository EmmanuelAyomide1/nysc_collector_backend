from django.utils.decorators import method_decorator

from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.serializers import (
    LoginSerializer,
    RegisterSerializer,
)
from apps.users.serializers import UserSerializer
from apps.authentication.utils import set_auth_cookies
from apps.common.constants import ACCESS_TOKEN_COOKIE_NAME, REFRESH_TOKEN_COOKIE_NAME


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
