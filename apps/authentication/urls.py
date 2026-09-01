from django.urls import path

from apps.authentication.views import (
    ForgotPasswordView,
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetRequestListView,
    RefreshView,
    RegisterView,
)

app_name = "authentication"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("refresh/", RefreshView.as_view(), name="refresh"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path("reset-password/", PasswordResetConfirmView.as_view(), name="reset-password"),
    path(
        "password-reset-requests/",
        PasswordResetRequestListView.as_view(),
        name="password-reset-requests",
    ),
]
