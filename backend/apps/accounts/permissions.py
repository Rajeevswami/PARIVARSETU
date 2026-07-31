"""RBAC for the accounts app — profile self-management vs. family-admin actions."""

from rest_framework.permissions import BasePermission

from apps.common.permissions import IsFamilyAdmin  # noqa: F401 — re-exported for accounts.views

from .models import UserRole


class IsSelfOrFamilyAdmin(BasePermission):
    """
    A user may always act on their own account. A family admin may act on
    any member who belongs to the same family_id.
    """

    message = "You can only manage your own profile."

    def has_object_permission(self, request, view, obj) -> bool:
        if obj.id == request.user.id:
            return True
        return (
            request.user.role == UserRole.FAMILY_ADMIN
            and obj.family_id is not None
            and obj.family_id == request.user.family_id
        )
