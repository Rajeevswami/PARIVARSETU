"""
Corrections never edit a posted Journal/LedgerEntry — they create a new
correcting Journal (posted normally through journal_service +
posting_service) and link it back to the original via AdjustmentEntry.
"""

from django.db import transaction

from apps.audit import services as audit_services

from ..models import AdjustmentEntry, Journal, TransactionType
from . import journal_service, posting_service


@transaction.atomic
def create_adjustment(
    *,
    actor,
    family_id,
    original_journal: Journal | None,
    lines: list[dict],
    reason: str,
    journal_date,
) -> AdjustmentEntry:
    adjustment_journal = journal_service.create_journal(
        family_id=family_id,
        transaction_type=TransactionType.ADJUSTMENT,
        journal_date=journal_date,
        lines=lines,
        reference_type="AdjustmentEntry",
        reference_id=original_journal.id if original_journal else "",
        description=f"Adjustment: {reason}",
        created_by=actor,
    )
    posting_service.post_journal(actor=actor, journal=adjustment_journal)

    adjustment = AdjustmentEntry.objects.create(
        family_id=family_id,
        original_journal=original_journal,
        adjustment_journal=adjustment_journal,
        reason=reason,
        created_by=actor,
    )

    audit_services.record(
        actor=actor,
        action=audit_services.AuditAction.LEDGER_ADJUSTMENT_CREATED,
        target_model="AdjustmentEntry",
        target_id=adjustment.id,
        family_id=family_id,
        metadata={"reason": reason},
    )
    return adjustment
