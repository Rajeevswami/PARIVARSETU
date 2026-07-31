"""Family-specific permission — most CRUD reuses apps.common.permissions."""

from rest_framework.permissions import BasePermission


class IsFamilyAdminOfObject(BasePermission):
    """Write access requires the requester to be the family_admin of this exact family."""

    message = "Only your family's admin can perform this action."

    def has_object_permission(self, request, view, obj) -> bool:
        family_id = obj.id if hasattr(obj, "family_code") else getattr(obj, "family_id", None)
        return (
            request.user.role == "family_admin"
            and request.user.family_id is not None
            and request.user.family_id == family_id
        )
