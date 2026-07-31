"""
Seeds each new Family with the standard 5 account groups and default
Chart of Accounts (Cash, Bank, UPI, Wallet, Expense, Income, Loan,
Borrow, Lend, Settlement, Adjustment, Family Balance, Household
Balance) plus an initial open FinancialPeriod for the current year.

Lives entirely in apps.ledger, watching apps.families.Family via a
signal — zero changes to the families app, same pattern as the
Expense module's default-category seeding.
"""

from datetime import date

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.families.models import Family

from .models import AccountGroup, FinancialPeriod, LedgerAccount, NormalBalance

# (group name, normal_balance, sort_order)
DEFAULT_GROUPS = [
    ("Assets", NormalBalance.DEBIT, 0),
    ("Liabilities", NormalBalance.CREDIT, 1),
    ("Income", NormalBalance.CREDIT, 2),
    ("Expenses", NormalBalance.DEBIT, 3),
    ("Equity", NormalBalance.CREDIT, 4),
]

# (code, name, group_name, is_system_account)
DEFAULT_ACCOUNTS = [
    ("1001", "Cash", "Assets"),
    ("1002", "Bank", "Assets"),
    ("1003", "UPI", "Assets"),
    ("1004", "Wallet", "Assets"),
    ("1005", "Lend", "Assets"),  # money lent out — a receivable
    ("1006", "Settlement Clearing", "Assets"),
    ("2001", "Loan", "Liabilities"),
    ("2002", "Borrow", "Liabilities"),
    ("3001", "Family Balance", "Equity"),
    ("3002", "Household Balance", "Equity"),
    ("3003", "Adjustment", "Equity"),
    ("4001", "Income", "Income"),
    ("5001", "Expense", "Expenses"),
]


@receiver(post_save, sender=Family)
def seed_default_chart_of_accounts(sender, instance: Family, created: bool, **kwargs):
    if not created:
        return

    groups_by_name = {}
    for name, normal_balance, sort_order in DEFAULT_GROUPS:
        groups_by_name[name] = AccountGroup.objects.create(
            family=instance, name=name, normal_balance=normal_balance, sort_order=sort_order
        )

    LedgerAccount.objects.bulk_create(
        [
            LedgerAccount(
                family=instance,
                account_code=code,
                account_name=name,
                account_group=groups_by_name[group_name],
                is_system_account=True,
            )
            for code, name, group_name in DEFAULT_ACCOUNTS
        ]
    )

    today = date.today()
    fy_start_year = today.year if today.month >= 4 else today.year - 1
    FinancialPeriod.objects.create(
        family=instance,
        name=f"FY {fy_start_year}-{str(fy_start_year + 1)[-2:]}",
        start_date=date(fy_start_year, 4, 1),
        end_date=date(fy_start_year + 1, 3, 31),
    )
