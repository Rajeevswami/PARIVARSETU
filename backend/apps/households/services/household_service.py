"""Business logic for Household CRUD, head-of-household changes, and deactivation."""

from apps.audit import services as audit_services
from apps.common.exceptions import ApplicationError

from ..models import Household


def create_household(*, admin, data: dict) -> Household:
    household = Household.objects.create(
        family_id=admin.family_id, created_by=admin, updated_by=admin, **data
    )
    audit_services.record(
        actor=admin,
        action=audit_services.AuditAction.HOUSEHOLD_CREATED,
        target_model="Household",
        target_id=household.id,
        family_id=admin.family_id,
    )
    return household


def update_household(*, admin, household: Household, data: dict) -> Household:
    for field, value in data.items():
        setattr(household, field, value)
    household.updated_by = admin
    household.save(update_fields=list(data.keys()) + ["updated_by", "updated_at"])

    audit_services.record(
        actor=admin,
        action=audit_services.AuditAction.HOUSEHOLD_UPDATED,
        target_model="Household",
        target_id=household.id,
        family_id=admin.family_id,
        metadata={"fields": list(data.keys())},
    )
    return household


def deactivate_household(*, admin, household: Household) -> Household:
    household.soft_delete(deleted_by=admin)
    audit_services.record(
        actor=admin,
        action=audit_services.AuditAction.HOUSEHOLD_DEACTIVATED,
        target_model="Household",
        target_id=household.id,
        family_id=admin.family_id,
    )
    return household


def change_head(*, admin, household: Household, member) -> Household:
    if member.family_id != household.family_id:
        raise ApplicationError(
            "The new head must belong to the same family as the household.",
            code="cross_family_action",
            status_code=403,
        )
    if member.household_id and member.household_id != household.id:
        raise ApplicationError(
            "The new head must already be a member of this household.", code="not_in_household"
        )

    household.head_of_household = member
    household.updated_by = admin
    household.save(update_fields=["head_of_household", "updated_by", "updated_at"])

    audit_services.record(
        actor=admin,
        action=audit_services.AuditAction.HOUSEHOLD_HEAD_CHANGED,
        target_model="Household",
        target_id=household.id,
        family_id=admin.family_id,
        metadata={"new_head_member_id": str(member.id)},
    )
    return household
