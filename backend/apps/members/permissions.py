"""Members app permissions — self-management vs. family-admin scope."""

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsSelfOrFamilyAdminMember(BasePermission):
    """A member may read/update their own profile; a family admin may manage any
    member within their own family."""

    message = "You can only manage your own member profile."

    def has_object_permission(self, request, view, obj) -> bool:
        if obj.user_id == request.user.id:
            return True
        is_family_admin = request.user.role == "family_admin"
        same_family = obj.family_id == request.user.family_id
        if request.method in SAFE_METHODS:
            return same_family
        return is_family_admin and same_family
