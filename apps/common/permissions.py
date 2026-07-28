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


class IsAdminOrSelf(BasePermission):
    """Grants access to authenticated users with the Administrator role or the user themselves."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return request.user.role == CustomUser.Role.ADMIN or request.user == obj
