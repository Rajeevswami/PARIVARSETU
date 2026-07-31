"""
Reusable RBAC / object-level permission classes, shared by every module
that scopes data by family_id.
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsFamilyMember(BasePermission):
    """Object must expose `family_id`; the user must belong to that same family."""

    message = "You are not a member of this family."

    def has_object_permission(self, request, view, obj):
        family_id = getattr(obj, "family_id", None)
        user_family_id = getattr(request.user, "family_id", None)
        return family_id is not None and family_id == user_family_id


class IsFamilyAdmin(BasePermission):
    """User's role must be family_admin. Family-scoped — combine with IsFamilyMember
    (or an object check) wherever cross-family access also needs to be ruled out."""

    message = "Only a family admin can perform this action."

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user and request.user.is_authenticated and request.user.role == "family_admin"
        )


class IsFamilyAdminOrReadOnly(BasePermission):
    """Read allowed to any family member; writes restricted to family admins."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return IsFamilyMember().has_object_permission(request, view, obj)
        return IsFamilyAdmin().has_permission(
            request, view
        ) and IsFamilyMember().has_object_permission(request, view, obj)


class IsOwner(BasePermission):
    """Object must expose `created_by_id`; only the creator may modify it."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return getattr(obj, "created_by_id", None) == request.user.id
