from rest_framework.permissions import BasePermission

from apps.users.models import CustomUser


class IsMember(BasePermission):
    """Grants access to authenticated users with the Member role."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == CustomUser.Role.MEMBER
        )


class IsAdministrator(BasePermission):
    """Grants access to authenticated users with the Administrator role."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == CustomUser.Role.ADMIN
        )
