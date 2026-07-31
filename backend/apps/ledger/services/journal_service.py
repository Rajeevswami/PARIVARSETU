"""
Business logic for Journal creation. A Journal always starts in draft
and is only posted (made immutable, LedgerEntry rows created) via
posting_service.post_journal — never posted directly here.
"""

from decimal import Decimal

from django.db import transaction

from apps.audit import services as audit_services
from apps.common.exceptions import ApplicationError

from ..models import Journal, JournalEntry, JournalEntryType, LedgerAccount


def _validate_balanced(lines: list[dict]) -> None:
    if not lines:
        raise ApplicationError("A journal must have at least one entry.", code="empty_journal")

    total_debit = sum(
        (line["amount"] for line in lines if line["entry_type"] == JournalEntryType.DEBIT),
        Decimal("0"),
    )
    total_credit = sum(
        (line["amount"] for line in lines if line["entry_type"] == JournalEntryType.CREDIT),
        Decimal("0"),
    )
    if total_debit != total_credit:
        message = (
            f"Journal is not balanced: total debit ({total_debit}) != "
            f"total credit ({total_credit})."
        )
        raise ApplicationError(message, code="unbalanced_journal")
    if total_debit <= 0:
        raise ApplicationError("A journal must post a non-zero amount.", code="zero_amount_journal")


@transaction.atomic
def create_journal(
    *,
    family_id,
    transaction_type: str,
    journal_date,
    lines: list[dict],
    reference_type: str = "",
    reference_id: str = "",
    description: str = "",
    created_by=None,
) -> Journal:
    """
    lines: [{"ledger_account": LedgerAccount | id, "entry_type": "debit"|"credit",
             "amount": Decimal, "description": str}]
    """
    _validate_balanced(lines)

    for line in lines:
        account = line["ledger_account"]
        account_id = account.id if isinstance(account, LedgerAccount) else account
        if not LedgerAccount.objects.filter(id=account_id, family_id=family_id).exists():
            raise ApplicationError(
                "All accounts in a journal must belong to the same family.",
                code="cross_family_account",
                status_code=403,
            )

    journal = Journal.objects.create(
        family_id=family_id,
        transaction_type=transaction_type,
        reference_type=reference_type,
        reference_id=str(reference_id) if reference_id else "",
        journal_date=journal_date,
        description=description,
        created_by=created_by,
    )

    JournalEntry.objects.bulk_create(
        [
            JournalEntry(
                journal=journal,
                ledger_account_id=(
                    line["ledger_account"].id
                    if isinstance(line["ledger_account"], LedgerAccount)
                    else line["ledger_account"]
                ),
                entry_type=line["entry_type"],
                amount=line["amount"],
                description=line.get("description", ""),
                sequence=i,
            )
            for i, line in enumerate(lines)
        ]
    )

    audit_services.record(
        actor=created_by,
        action=audit_services.AuditAction.LEDGER_JOURNAL_CREATED,
        target_model="Journal",
        target_id=journal.id,
        family_id=family_id,
        metadata={"transaction_type": transaction_type},
    )
    return journal
