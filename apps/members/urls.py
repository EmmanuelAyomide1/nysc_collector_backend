from django.urls import path
from rest_framework import routers

from apps.members.views import ActiveBatchListView, MemberViewSet

app_name = "members"

router = routers.DefaultRouter()
router.register("members", MemberViewSet, basename="members")

urlpatterns = [
    path("batches/", ActiveBatchListView.as_view(), name="active-batches"),
] + router.urls
