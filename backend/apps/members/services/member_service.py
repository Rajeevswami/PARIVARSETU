"""Business logic for Member profile management and transfers between households."""

from apps.audit import services as audit_services
from apps.common.exceptions import ApplicationError

from ..models import Member


def create_member_for_existing_user(*, admin, target_user, data: dict) -> Member:
    """
    Family admin adds a Member profile for a User who already has an
    account but doesn't belong to a family yet (direct provisioning,
    separate from the invitation flow).
    """
    if target_user.family_id is not None:
        raise ApplicationError("That user already belongs to a family.", code="already_in_family")

    household = data.pop("household", None)
    if household is not None and household.family_id != admin.family_id:
        raise ApplicationError(
            "The household must belong to your family.", code="cross_family_action", status_code=403
        )

    member = Member.objects.create(
        user=target_user,
        family_id=admin.family_id,
        household=household,
        created_by=admin,
        updated_by=admin,
        **data,
    )

    target_user.family_id = admin.family_id
    target_user.household = household
    target_user.save(update_fields=["family", "household"])

    audit_services.record(
        actor=admin,
        action=audit_services.AuditAction.MEMBER_PROFILE_CREATED,
        target_model="Member",
        target_id=member.id,
        family_id=admin.family_id,
    )
    return member


def update_member(*, actor, member: Member, data: dict) -> Member:
    for field, value in data.items():
        setattr(member, field, value)
    member.updated_by = actor
    member.save(update_fields=list(data.keys()) + ["updated_by", "updated_at"])

    audit_services.record(
        actor=actor,
        action=audit_services.AuditAction.MEMBER_PROFILE_UPDATED,
        target_model="Member",
        target_id=member.id,
        family_id=member.family_id,
        metadata={"fields": list(data.keys())},
    )
    return member


def transfer_member(*, admin, member: Member, new_household) -> Member:
    if new_household is not None and new_household.family_id != admin.family_id:
        raise ApplicationError(
            "You can only transfer members to a household within your own family.",
            code="cross_family_action",
            status_code=403,
        )
    if member.family_id != admin.family_id:
        raise ApplicationError(
            "You can only transfer members within your own family.",
            code="cross_family_action",
            status_code=403,
        )

    old_household_id = member.household_id
    member.household = new_household
    member.updated_by = admin
    member.save(update_fields=["household", "updated_by", "updated_at"])

    # Keep the denormalized User.household in sync.
    member.user.household = new_household
    member.user.save(update_fields=["household"])

    audit_services.record(
        actor=admin,
        action=audit_services.AuditAction.MEMBER_TRANSFERRED,
        target_model="Member",
        target_id=member.id,
        family_id=admin.family_id,
        metadata={
            "from_household_id": str(old_household_id) if old_household_id else None,
            "to_household_id": str(new_household.id) if new_household else None,
        },
    )
    return member
