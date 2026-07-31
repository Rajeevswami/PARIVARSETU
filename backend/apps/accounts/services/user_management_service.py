"""
Family-admin actions on member accounts. Scoped purely by `family_id` on
the User model — no dependency on the (not-yet-built) Family module.
"""

import secrets

from apps.audit import services as audit_services
from apps.common.exceptions import ApplicationError

from ..models import UserStatus


def _assert_same_family(admin, member) -> None:
    if member.family_id is None or member.family_id != admin.family_id:
        raise ApplicationError(
            "You can only manage members of your own family.",
            code="cross_family_action",
            status_code=403,
        )


def reset_member_password(*, admin, member) -> str:
    _assert_same_family(admin, member)

    temp_password = secrets.token_urlsafe(9)
    member.set_password(temp_password)
    member.save(update_fields=["password"])

    audit_services.record(
        actor=admin,
        action=audit_services.AuditAction.MEMBER_PASSWORD_RESET,
        target_model="User",
        target_id=member.id,
        family_id=admin.family_id,
    )
    return temp_password


def deactivate_member(*, admin, member) -> "User":  # noqa: F821
    _assert_same_family(admin, member)

    member.status = UserStatus.INACTIVE
    member.is_active = False
    member.save(update_fields=["status", "is_active"])

    audit_services.record(
        actor=admin,
        action=audit_services.AuditAction.MEMBER_DEACTIVATED,
        target_model="User",
        target_id=member.id,
        family_id=admin.family_id,
    )
    return member


def reactivate_member(*, admin, member) -> "User":  # noqa: F821
    _assert_same_family(admin, member)

    member.status = UserStatus.ACTIVE
    member.is_active = True
    member.save(update_fields=["status", "is_active"])

    audit_services.record(
        actor=admin,
        action=audit_services.AuditAction.MEMBER_REACTIVATED,
        target_model="User",
        target_id=member.id,
        family_id=admin.family_id,
    )
    return member
