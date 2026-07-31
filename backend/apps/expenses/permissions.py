"""
Expense permission rules:
- Family Admin: full access (view/create/edit/cancel/settle anything in family).
- Member: can create their own expenses (paid_by = themself), edit their
  own, view whatever their visibility allows, but can never delete/cancel.
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission


def _member_of(request):
    return getattr(request.user, "member_profile", None)


class CanViewExpense(BasePermission):
    message = "You don't have access to this expense."

    def has_object_permission(self, request, view, obj) -> bool:
        if obj.family_id != request.user.family_id:
            return False
        if request.user.role == "family_admin":
            return True

        member = _member_of(request)
        if member is None:
            return False
        if obj.visibility == "family":
            return True
        if obj.visibility == "household":
            return member.household_id is not None and member.household_id == obj.household_id
        # private
        return obj.paid_by_id == member.id


class CanEditExpense(BasePermission):
    message = "You can only edit your own expenses."

    def has_object_permission(self, request, view, obj) -> bool:
        if request.method in SAFE_METHODS:
            return CanViewExpense().has_object_permission(request, view, obj)
        if request.user.role == "family_admin":
            return True
        member = _member_of(request)
        return member is not None and obj.paid_by_id == member.id


class IsFamilyAdminForDestructive(BasePermission):
    """Cancel/restore are admin-only — members can never delete an expense."""

    message = "Only a family admin can cancel or restore an expense."

    def has_permission(self, request, view) -> bool:
        return bool(request.user.is_authenticated and request.user.role == "family_admin")
