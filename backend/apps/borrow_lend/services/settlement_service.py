"""
Business logic for recording settlements against a BorrowTransaction or
LendTransaction. Generic over both via reference_type/reference_id —
same over-settlement prevention as the Expense module's SettlementService.
"""

from decimal import Decimal

from apps.audit import services as audit_services
from apps.common.exceptions import ApplicationError
from apps.loans.models import LedgerPostingEvent
from apps.loans.services import ledger_hook

from ..models import (
    BorrowTransaction,
    LendTransaction,
    Settlement,
    SettlementReferenceType,
    TransactionStatus,
)

_MODEL_BY_TYPE = {
    SettlementReferenceType.BORROW: BorrowTransaction,
    SettlementReferenceType.LEND: LendTransaction,
}


def _get_transaction(reference_type: str, reference_id):
    model = _MODEL_BY_TYPE.get(reference_type)
    if model is None:
        raise ApplicationError("Unknown reference_type.", code="invalid_reference_type")
    try:
        return model.objects.get(id=reference_id)
    except model.DoesNotExist as exc:
        raise ApplicationError("Transaction not found.", code="not_found", status_code=404) from exc


def record_settlement(
    *,
    actor,
    reference_type: str,
    reference_id,
    member_id,
    amount: Decimal,
    settlement_date,
    remarks: str = "",
) -> Settlement:
    transaction = _get_transaction(reference_type, reference_id)

    if amount <= 0:
        raise ApplicationError(
            "Settlement amount must be greater than zero.", code="invalid_amount"
        )

    if transaction.settled_amount + amount > transaction.amount:
        raise ApplicationError(
            "This settlement would exceed the transaction's total amount "
            f"(amount: {transaction.amount}, already settled: {transaction.settled_amount}).",
            code="duplicate_or_excess_settlement",
        )

    new_settled_total = transaction.settled_amount + amount
    remaining = transaction.amount - new_settled_total

    settlement = Settlement.objects.create(
        reference_type=reference_type,
        reference_id=reference_id,
        member_id=member_id,
        amount=amount,
        settled_amount=new_settled_total,
        remaining_amount=remaining,
        settlement_date=settlement_date,
        remarks=remarks,
        created_by=actor,
    )

    transaction.settled_amount = new_settled_total
    transaction.status = (
        TransactionStatus.SETTLED if remaining <= 0 else TransactionStatus.PARTIALLY_SETTLED
    )
    transaction.save(update_fields=["settled_amount", "status", "updated_at"])

    ledger_hook.queue_posting(
        family_id=transaction.family_id,
        event_type=LedgerPostingEvent.SETTLEMENT_RECORDED,
        amount=amount,
        source_model="Settlement",
        source_id=settlement.id,
        metadata={"reference_type": reference_type, "reference_id": str(reference_id)},
    )
    audit_services.record(
        actor=actor,
        action=audit_services.AuditAction.BORROW_LEND_SETTLEMENT_RECORDED,
        target_model="Settlement",
        target_id=settlement.id,
        family_id=transaction.family_id,
        metadata={"amount": str(amount)},
    )
    return settlement
