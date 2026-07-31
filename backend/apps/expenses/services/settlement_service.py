"""
Business logic for recording settlements against an expense participant's
share. Prevents duplicate/over-settlement: the sum of all recorded
settlements for a participant can never exceed their share_amount.
"""

from decimal import Decimal

from apps.audit import services as audit_services
from apps.common.exceptions import ApplicationError

from ..models import (
    Expense,
    ExpenseParticipant,
    ExpenseSettlement,
    ExpenseSettlementStatus,
    LedgerPostingEvent,
)
from . import ledger_hook


def record_settlement(
    *, actor, expense: Expense, member_id, paid_amount: Decimal, settlement_date, remarks: str = ""
) -> ExpenseSettlement:
    try:
        participant = ExpenseParticipant.objects.select_related("member").get(
            expense=expense, member_id=member_id
        )
    except ExpenseParticipant.DoesNotExist as exc:
        raise ApplicationError(
            "This member is not a participant in this expense.", code="not_a_participant"
        ) from exc

    if paid_amount <= 0:
        raise ApplicationError(
            "Settlement amount must be greater than zero.", code="invalid_amount"
        )

    already_settled = ExpenseSettlement.objects.filter(
        expense=expense, member_id=member_id, status=ExpenseSettlementStatus.RECORDED
    )
    total_settled_so_far = sum((s.paid_amount for s in already_settled), Decimal("0"))

    if total_settled_so_far + paid_amount > participant.share_amount:
        raise ApplicationError(
            "This settlement would exceed the participant's share amount "
            f"(share: {participant.share_amount}, already settled: {total_settled_so_far}).",
            code="duplicate_or_excess_settlement",
        )

    remaining = participant.share_amount - (total_settled_so_far + paid_amount)
    settlement = ExpenseSettlement.objects.create(
        expense=expense,
        member_id=member_id,
        paid_amount=paid_amount,
        received_amount=paid_amount,
        remaining_amount=remaining,
        settlement_date=settlement_date,
        remarks=remarks,
        created_by=actor,
    )

    participant.settled_amount = total_settled_so_far + paid_amount
    participant.recompute()

    ledger_hook.queue_posting(
        expense=expense,
        event_type=LedgerPostingEvent.SETTLEMENT_RECORDED,
        amount=paid_amount,
        metadata={"member_id": str(member_id), "settlement_id": str(settlement.id)},
    )

    audit_services.record(
        actor=actor,
        action=audit_services.AuditAction.EXPENSE_SETTLEMENT_RECORDED,
        target_model="ExpenseSettlement",
        target_id=settlement.id,
        family_id=expense.family_id,
        metadata={"amount": str(paid_amount), "member_id": str(member_id)},
    )

    # If every participant is now fully settled, the expense itself is settled.
    from ..models import ExpenseParticipantStatus, ExpenseStatus

    if not expense.participants.exclude(status=ExpenseParticipantStatus.SETTLED).exists():
        expense.status = ExpenseStatus.SETTLED
        expense.save(update_fields=["status", "updated_at"])

    return settlement
