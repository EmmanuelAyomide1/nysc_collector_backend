from rest_framework import routers

from apps.members.views import MemberViewSet

app_name = "members"

router = routers.DefaultRouter()
router.register("members", MemberViewSet, basename="members")

urlpatterns = router.urls
