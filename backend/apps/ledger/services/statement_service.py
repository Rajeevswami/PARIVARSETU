"""
Read-side statement generation. Cash Book / Bank Book / Ledger Book are
all the same underlying query (an account statement) filtered to a
specific account — implemented once here rather than as separate
mechanisms, since duplicating identical query logic under three names
would violate the project's no-duplication convention.
"""

from ..models import LedgerAccount, LedgerEntry


def account_statement(*, family_id, account_id, date_from=None, date_to=None) -> dict:
    account = LedgerAccount.objects.get(id=account_id, family_id=family_id)
    entries = LedgerEntry.objects.filter(ledger_account=account).order_by(
        "transaction_date", "created_at"
    )
    if date_from:
        entries = entries.filter(transaction_date__gte=date_from)
    if date_to:
        entries = entries.filter(transaction_date__lte=date_to)

    return {
        "account_code": account.account_code,
        "account_name": account.account_name,
        "entries": [
            {
                "ledger_number": e.ledger_number,
                "transaction_date": e.transaction_date,
                "opening_balance": str(e.opening_balance),
                "debit": str(e.debit),
                "credit": str(e.credit),
                "closing_balance": str(e.closing_balance),
                "remarks": e.remarks,
                "journal_number": e.journal.journal_number,
            }
            for e in entries
        ],
    }


def cash_book(*, family_id, date_from=None, date_to=None) -> dict:
    account = LedgerAccount.objects.filter(family_id=family_id, account_code="1001").first()
    if account is None:
        return {"account_code": "1001", "account_name": "Cash", "entries": []}
    return account_statement(
        family_id=family_id, account_id=account.id, date_from=date_from, date_to=date_to
    )


def bank_book(*, family_id, date_from=None, date_to=None) -> dict:
    account = LedgerAccount.objects.filter(family_id=family_id, account_code="1002").first()
    if account is None:
        return {"account_code": "1002", "account_name": "Bank", "entries": []}
    return account_statement(
        family_id=family_id, account_id=account.id, date_from=date_from, date_to=date_to
    )


def journal_register(*, family_id, date_from=None, date_to=None, status=None):
    from ..models import Journal

    qs = Journal.objects.filter(family_id=family_id).order_by("-journal_date", "-created_at")
    if date_from:
        qs = qs.filter(journal_date__gte=date_from)
    if date_to:
        qs = qs.filter(journal_date__lte=date_to)
    if status:
        qs = qs.filter(status=status)
    return qs


def member_statement(*, family_id, member) -> dict:
    """
    A member's personal balance isn't tracked as its own LedgerAccount
    (the family/household balance accounts are shared) — this surfaces
    what's specific to that member: expenses they paid, loans they're a
    party to. Kept intentionally light; a dedicated per-member ledger
    account is a natural follow-up if member-level P&L is needed later.
    """
    from django.db.models import Q

    from apps.expenses.models import Expense
    from apps.loans.models import Loan

    expenses_paid = Expense.objects.filter(family_id=family_id, paid_by=member, is_deleted=False)
    loans = Loan.objects.filter(family_id=family_id, is_deleted=False).filter(
        Q(borrower=member) | Q(lender=member)
    )
    return {
        "member_id": str(member.id),
        "member_name": member.display_name,
        "total_expenses_paid": str(sum((e.amount for e in expenses_paid), 0)),
        "loan_count": loans.count(),
    }
