"""
Closes a FinancialPeriod: verifies no draft journals remain within it,
snapshots every account's closing balance, creates the next period plus
its OpeningBalance rows (carry-forward), and marks the period closed.
Closed periods reject new postings (enforced in posting_service).
"""

from datetime import timedelta

from django.db import transaction

from apps.audit import services as audit_services
from apps.common.exceptions import ApplicationError

from ..models import (
    AccountBalance,
    ClosingPeriod,
    FinancialPeriod,
    FinancialPeriodStatus,
    JournalStatus,
    LedgerAccount,
    OpeningBalance,
)


@transaction.atomic
def close_period(*, actor, period: FinancialPeriod) -> ClosingPeriod:
    if period.status != FinancialPeriodStatus.OPEN:
        raise ApplicationError(f"Period '{period.name}' is already closed.", code="already_closed")

    draft_count = period.family.journals.filter(
        status=JournalStatus.DRAFT,
        journal_date__gte=period.start_date,
        journal_date__lte=period.end_date,
    ).count()
    if draft_count:
        message = (
            f"{draft_count} draft journal(s) remain in this period — "
            "post or discard them before closing."
        )
        raise ApplicationError(message, code="draft_journals_remain")

    accounts = LedgerAccount.objects.filter(
        family_id=period.family_id, status="active"
    ).select_related("balance")
    snapshot = {}
    for account in accounts:
        balance = getattr(account, "balance", None)
        closing_balance = balance.current_balance if balance else 0
        snapshot[account.account_code] = {
            "account_name": account.account_name,
            "closing_balance": str(closing_balance),
        }

    next_period, _ = FinancialPeriod.objects.get_or_create(
        family_id=period.family_id,
        start_date=period.end_date + timedelta(days=1),
        defaults={
            "name": f"Period starting {period.end_date + timedelta(days=1)}",
            "end_date": period.end_date.replace(year=period.end_date.year + 1),
        },
    )

    for account in accounts:
        balance = getattr(account, "balance", None)
        opening_amount = balance.current_balance if balance else 0
        OpeningBalance.objects.update_or_create(
            ledger_account=account,
            financial_period=next_period,
            defaults={
                "family_id": period.family_id,
                "amount": abs(opening_amount),
                "entry_type": "debit" if opening_amount >= 0 else "credit",
                "created_by": actor,
            },
        )
        AccountBalance.objects.filter(account=account).update(opening_balance=opening_amount)

    period.status = FinancialPeriodStatus.CLOSED
    period.save(update_fields=["status"])

    closing = ClosingPeriod.objects.create(
        family_id=period.family_id,
        financial_period=period,
        closing_balances_snapshot=snapshot,
        closed_by=actor,
    )

    audit_services.record(
        actor=actor,
        action=audit_services.AuditAction.LEDGER_PERIOD_CLOSED,
        target_model="FinancialPeriod",
        target_id=period.id,
        family_id=period.family_id,
        metadata={"period_name": period.name},
    )
    return closing
