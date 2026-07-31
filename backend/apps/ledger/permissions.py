"""
Ledger permissions: Family Admin has full access (create manual
journals, post, adjust, view all statements). Members can view
statements they're allowed to see but can never modify the ledger.
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.common.permissions import IsFamilyAdmin  # noqa: F401 — re-exported for views


class IsFamilyAdminOrReadOnly(BasePermission):
    message = "Only a family admin can modify the ledger."

    def has_permission(self, request, view) -> bool:
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user.is_authenticated and request.user.role == "family_admin")
