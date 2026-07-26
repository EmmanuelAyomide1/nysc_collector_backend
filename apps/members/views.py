from django.contrib.auth import get_user_model

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response


from apps.common.permissions import IsAdminOrSelf, IsAdministrator
from apps.members.serializers import MemberSerializer, MemberUpdateSerializer

User = get_user_model()


class MemberViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = MemberSerializer
    permission_classes = [IsAdministrator]
    http_method_names = ["get", "put", "patch", "post"]

    def get_permissions(self):
        if self.action in ["list", "update", "partial_update"]:
            return [IsAdministrator()]

        if self.action in ["retrieve"]:
            return [IsAdminOrSelf()]

        return [IsAdministrator()]

    def get_serializer_class(self):
        if self.action in ["update", "partial_update"]:
            return MemberUpdateSerializer
        return super().get_serializer_class()

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)

        if (
            isinstance(response, Response)
            and 200 <= response.status_code < 300
            and isinstance(response.data, dict)
            and "success" not in response.data
        ):
            response.data = {
                "success": True,
                "data": response.data,
            }

        return response

    @action(detail=True, methods=["post"], url_path="activate-member")
    def activate_member(self, request, pk=None):
        member = self.get_object()
        member.is_active = True
        member.save(update_fields=["is_active"])
        return Response({"success": True, "data": self.serializer_class(member).data})

    @action(detail=True, methods=["post"], url_path="deactivate-member")
    def deactivate_member(self, request, pk=None):
        member = self.get_object()
        member.is_active = False
        member.save(update_fields=["is_active"])
        return Response({"success": True, "data": self.serializer_class(member).data})
