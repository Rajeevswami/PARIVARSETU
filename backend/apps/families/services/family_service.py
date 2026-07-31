"""Business logic for Family creation/update. Views stay thin and call these."""

from apps.audit import services as audit_services
from apps.common.exceptions import ApplicationError

from ..models import Family


def create_family(*, user, data: dict) -> Family:
    if user.family_id is not None:
        raise ApplicationError(
            "You already belong to a family. Leave it before creating a new one.",
            code="already_in_family",
        )

    family = Family.objects.create(created_by=user, updated_by=user, **data)

    # The creator becomes the Family Admin and gets a Member profile —
    # bootstraps the very first member of a brand-new family.
    from apps.accounts.models import UserRole, UserStatus
    from apps.members.models import Member

    user.family = family
    user.role = UserRole.FAMILY_ADMIN
    if user.status == UserStatus.PENDING_VERIFICATION:
        user.status = UserStatus.ACTIVE
    user.save(update_fields=["family", "role", "status"])

    Member.objects.create(
        user=user,
        family=family,
        display_name=user.get_full_name() or user.email,
        created_by=user,
        updated_by=user,
    )

    audit_services.record(
        actor=user,
        action=audit_services.AuditAction.FAMILY_CREATED,
        target_model="Family",
        target_id=family.id,
        family_id=family.id,
    )
    return family


def update_family(*, user, family: Family, data: dict) -> Family:
    for field, value in data.items():
        setattr(family, field, value)
    family.updated_by = user
    family.save(update_fields=list(data.keys()) + ["updated_by", "updated_at"])

    audit_services.record(
        actor=user,
        action=audit_services.AuditAction.FAMILY_UPDATED,
        target_model="Family",
        target_id=family.id,
        family_id=family.id,
        metadata={"fields": list(data.keys())},
    )
    return family
