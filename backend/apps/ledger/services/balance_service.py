"""Read-side queries for account/member/household/family balances and trial balance."""

from decimal import Decimal

from django.db.models import Q, Sum

from ..models import AccountBalance, LedgerAccount, NormalBalance


def get_account_balance(account: LedgerAccount) -> Decimal:
    balance = AccountBalance.objects.filter(account=account).first()
    return balance.current_balance if balance else Decimal("0")


def get_trial_balance(family_id) -> dict:
    """
    Returns every account's debit_total/credit_total, plus the overall
    grand totals — a balanced ledger always has grand_debit == grand_credit.
    """
    accounts = LedgerAccount.objects.filter(family_id=family_id, status="active").select_related(
        "account_group", "balance"
    )

    rows = []
    grand_debit = Decimal("0")
    grand_credit = Decimal("0")

    for account in accounts:
        balance = getattr(account, "balance", None)
        debit_total = balance.debit_total if balance else Decimal("0")
        credit_total = balance.credit_total if balance else Decimal("0")
        current = balance.current_balance if balance else Decimal("0")

        # Trial balance convention: show the balance on its natural side.
        if account.account_group.normal_balance == NormalBalance.DEBIT:
            debit_col = current if current >= 0 else Decimal("0")
            credit_col = -current if current < 0 else Decimal("0")
        else:
            credit_col = current if current >= 0 else Decimal("0")
            debit_col = -current if current < 0 else Decimal("0")

        grand_debit += debit_col
        grand_credit += credit_col

        rows.append(
            {
                "account_code": account.account_code,
                "account_name": account.account_name,
                "account_group": account.account_group.name,
                "debit_total": str(debit_total),
                "credit_total": str(credit_total),
                "balance": str(debit_col),
                "credit_balance": str(credit_col),
            }
        )

    return {"rows": rows, "grand_debit": str(grand_debit), "grand_credit": str(grand_credit)}


def get_family_balance(family_id) -> Decimal:
    account = LedgerAccount.objects.filter(family_id=family_id, account_code="3001").first()
    return get_account_balance(account) if account else Decimal("0")


def get_household_balance(family_id) -> Decimal:
    account = LedgerAccount.objects.filter(family_id=family_id, account_code="3002").first()
    return get_account_balance(account) if account else Decimal("0")


def get_cash_and_bank_summary(family_id) -> dict:
    accounts = LedgerAccount.objects.filter(
        family_id=family_id, account_code__in=["1001", "1002", "1003", "1004"]
    ).select_related("balance")
    return {a.account_name: str(get_account_balance(a)) for a in accounts}


def get_income_expense_summary(family_id) -> dict:
    totals = AccountBalance.objects.filter(
        account__family_id=family_id, account__account_code__in=["4001", "5001"]
    ).aggregate(
        income=Sum("current_balance", filter=Q(account__account_code="4001")),
        expense=Sum("current_balance", filter=Q(account__account_code="5001")),
    )
    return {
        "income": str(totals["income"] or Decimal("0")),
        "expense": str(totals["expense"] or Decimal("0")),
    }
