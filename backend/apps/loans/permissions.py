"""
Loan permission rules:
- Family Admin: full access.
- Member: can create their own borrow requests (as borrower), view
  records they're a party to (borrower or lender) or that are visible
  at the family level, edit their own drafts, never delete.
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission


def _member_of(request):
    return getattr(request.user, "member_profile", None)


class CanViewLoan(BasePermission):
    message = "You don't have access to this loan."

    def has_object_permission(self, request, view, obj) -> bool:
        if obj.family_id != request.user.family_id:
            return False
        if request.user.role == "family_admin":
            return True
        member = _member_of(request)
        if member is None:
            return False
        return obj.borrower_id == member.id or obj.lender_id == member.id


class CanEditLoan(BasePermission):
    message = "You can only edit your own draft loans."

    def has_object_permission(self, request, view, obj) -> bool:
        if request.method in SAFE_METHODS:
            return CanViewLoan().has_object_permission(request, view, obj)
        if request.user.role == "family_admin":
            return True
        member = _member_of(request)
        if member is None:
            return False
        return obj.borrower_id == member.id and obj.status == "draft"


class IsFamilyAdminForDestructive(BasePermission):
    message = "Only a family admin can cancel or restore a loan."

    def has_permission(self, request, view) -> bool:
        return bool(request.user.is_authenticated and request.user.role == "family_admin")
