"""
The only place a Journal actually gets posted: validates the financial
period is open, re-validates balance (defense in depth), creates one
immutable LedgerEntry per JournalEntry line with an opening/closing
balance snapshot, and atomically updates each account's running
AccountBalance. A Journal can only be posted once — its status flips
from draft to posted, and posted Journals are never edited again.
"""

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.audit import services as audit_services
from apps.common.exceptions import ApplicationError

from ..models import (
    AccountBalance,
    FinancialPeriod,
    Journal,
    JournalEntryType,
    JournalStatus,
    LedgerEntry,
    NormalBalance,
)


def _assert_period_open(family_id, journal_date) -> None:
    period = FinancialPeriod.objects.filter(
        family_id=family_id, start_date__lte=journal_date, end_date__gte=journal_date
    ).first()
    if period is None:
        raise ApplicationError(
            "No financial period covers this journal date.", code="no_financial_period"
        )
    if period.status != "open":
        raise ApplicationError(
            f"The financial period '{period.name}' is closed — cannot post to it.",
            code="period_closed",
        )


@transaction.atomic
def post_journal(*, actor, journal: Journal) -> Journal:
    if journal.status != JournalStatus.DRAFT:
        raise ApplicationError(
            f"Journal {journal.journal_number} is already {journal.status} — cannot post again.",
            code="duplicate_posting",
        )

    entries = list(
        journal.entries.select_related("ledger_account", "ledger_account__account_group")
    )
    if not entries:
        raise ApplicationError("Cannot post an empty journal.", code="empty_journal")

    total_debit = sum(
        (e.amount for e in entries if e.entry_type == JournalEntryType.DEBIT), Decimal("0")
    )
    total_credit = sum(
        (e.amount for e in entries if e.entry_type == JournalEntryType.CREDIT), Decimal("0")
    )
    if total_debit != total_credit:
        raise ApplicationError(
            f"Journal is not balanced: debit ({total_debit}) != credit ({total_credit}).",
            code="unbalanced_journal",
        )

    _assert_period_open(journal.family_id, journal.journal_date)

    for entry in entries:
        account = entry.ledger_account
        balance, _ = AccountBalance.objects.select_for_update().get_or_create(
            account=account, defaults={"opening_balance": Decimal("0")}
        )

        opening = balance.current_balance
        debit_amount = entry.amount if entry.entry_type == JournalEntryType.DEBIT else Decimal("0")
        credit_amount = (
            entry.amount if entry.entry_type == JournalEntryType.CREDIT else Decimal("0")
        )

        if account.account_group.normal_balance == NormalBalance.DEBIT:
            delta = debit_amount - credit_amount
        else:
            delta = credit_amount - debit_amount
        closing = opening + delta

        LedgerEntry.objects.create(
            journal=journal,
            ledger_account=account,
            transaction_date=journal.journal_date,
            opening_balance=opening,
            debit=debit_amount,
            credit=credit_amount,
            closing_balance=closing,
            reference_number=journal.journal_number,
            remarks=entry.description,
        )

        balance.debit_total += debit_amount
        balance.credit_total += credit_amount
        balance.current_balance = closing
        balance.save(
            update_fields=["debit_total", "credit_total", "current_balance", "last_updated"]
        )

    journal.status = JournalStatus.POSTED
    journal.posted_at = timezone.now()
    journal.save(update_fields=["status", "posted_at"])

    audit_services.record(
        actor=actor,
        action=audit_services.AuditAction.LEDGER_JOURNAL_POSTED,
        target_model="Journal",
        target_id=journal.id,
        family_id=journal.family_id,
        metadata={"journal_number": journal.journal_number},
    )
    return journal
