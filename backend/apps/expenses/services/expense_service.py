"""Business logic for Expense CRUD, splits, and cancellation."""

from decimal import Decimal

from apps.audit import services as audit_services
from apps.common.exceptions import ApplicationError
from apps.households.models import Household
from apps.members.models import Member

from ..models import Expense, ExpenseParticipant, ExpenseStatus, LedgerPostingEvent
from . import ledger_hook
from .splits import calculate_shares


def _assert_member_in_family(member: Member, family_id) -> None:
    if member.family_id != family_id:
        raise ApplicationError(
            "All participants must belong to the same family.",
            code="cross_family_participant",
            status_code=403,
        )


def _assert_household_in_family(household: Household | None, family_id) -> None:
    if household is not None and household.family_id != family_id:
        raise ApplicationError(
            "The household must belong to the same family as the expense.",
            code="cross_family_household",
            status_code=403,
        )


def create_expense(*, actor, family_id, data: dict, split_type: str, split_data) -> Expense:
    paid_by: Member = data["paid_by"]
    _assert_member_in_family(paid_by, family_id)
    _assert_household_in_family(data.get("household"), family_id)

    expense = Expense.objects.create(
        family_id=family_id, created_by=actor, updated_by=actor, **data
    )

    shares = calculate_shares(split_type=split_type, total=expense.amount, split_data=split_data)
    participants = []
    for member_id, share_amount in shares.items():
        member = Member.objects.get(id=member_id)
        _assert_member_in_family(member, family_id)
        participant = ExpenseParticipant(
            expense=expense, member=member, share_amount=share_amount, pending_amount=share_amount
        )
        if split_type == "percentage":
            participant.share_percentage = Decimal(str(split_data[member_id]))
        participants.append(participant)
    ExpenseParticipant.objects.bulk_create(participants)

    ledger_hook.queue_posting(
        expense=expense,
        event_type=LedgerPostingEvent.EXPENSE_CREATED,
        amount=expense.amount,
        metadata={"split_type": split_type},
    )

    audit_services.record(
        actor=actor,
        action=audit_services.AuditAction.EXPENSE_CREATED,
        target_model="Expense",
        target_id=expense.id,
        family_id=family_id,
        metadata={"amount": str(expense.amount), "split_type": split_type},
    )
    return expense


def update_expense(*, actor, expense: Expense, data: dict) -> Expense:
    if "household" in data:
        _assert_household_in_family(data["household"], expense.family_id)
    if "paid_by" in data:
        _assert_member_in_family(data["paid_by"], expense.family_id)

    for field, value in data.items():
        setattr(expense, field, value)
    expense.updated_by = actor
    expense.save(update_fields=list(data.keys()) + ["updated_by", "updated_at"])

    ledger_hook.queue_posting(
        expense=expense,
        event_type=LedgerPostingEvent.EXPENSE_UPDATED,
        amount=expense.amount,
        metadata={"fields": list(data.keys())},
    )

    audit_services.record(
        actor=actor,
        action=audit_services.AuditAction.EXPENSE_UPDATED,
        target_model="Expense",
        target_id=expense.id,
        family_id=expense.family_id,
        metadata={"fields": list(data.keys())},
    )
    return expense


def cancel_expense(*, actor, expense: Expense) -> Expense:
    expense.soft_delete(deleted_by=actor)

    ledger_hook.queue_posting(
        expense=expense, event_type=LedgerPostingEvent.EXPENSE_CANCELLED, amount=expense.amount
    )
    audit_services.record(
        actor=actor,
        action=audit_services.AuditAction.EXPENSE_CANCELLED,
        target_model="Expense",
        target_id=expense.id,
        family_id=expense.family_id,
    )
    return expense


def restore_expense(*, actor, expense: Expense) -> Expense:
    expense.is_deleted = False
    expense.status = ExpenseStatus.PENDING
    expense.deleted_at = None
    expense.deleted_by = None
    expense.updated_by = actor
    expense.save(
        update_fields=[
            "is_deleted",
            "status",
            "deleted_at",
            "deleted_by",
            "updated_by",
            "updated_at",
        ]
    )

    audit_services.record(
        actor=actor,
        action=audit_services.AuditAction.EXPENSE_RESTORED,
        target_model="Expense",
        target_id=expense.id,
        family_id=expense.family_id,
    )
    return expense
