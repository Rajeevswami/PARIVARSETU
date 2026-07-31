"""Borrow/Lend permissions — same shape as Loan: admin full access, member sees/edits their own."""

from rest_framework.permissions import BasePermission


def _member_of(request):
    return getattr(request.user, "member_profile", None)


class CanViewBorrow(BasePermission):
    message = "You don't have access to this borrow transaction."

    def has_object_permission(self, request, view, obj) -> bool:
        if obj.family_id != request.user.family_id:
            return False
        if request.user.role == "family_admin":
            return True
        member = _member_of(request)
        return member is not None and (obj.borrower_id == member.id or obj.lender_id == member.id)


class CanViewLend(BasePermission):
    message = "You don't have access to this lend transaction."

    def has_object_permission(self, request, view, obj) -> bool:
        if obj.family_id != request.user.family_id:
            return False
        if request.user.role == "family_admin":
            return True
        member = _member_of(request)
        return member is not None and (obj.giver_id == member.id or obj.receiver_id == member.id)
