from django.urls import path
from apps.users.views import CurrentUserView

urlpatterns = [
    path("me/", CurrentUserView.as_view(), name="current-user"),
]
