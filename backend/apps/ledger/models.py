"""
Ledger Engine — the double-entry accounting core every financial module
posts through.

NOTE on ChartOfAccount vs LedgerAccount: the spec lists these as two
separate models with overlapping fields (account_code, account_name,
account_group, parent_account, family, ...). In real double-entry
accounting these are the same concept — the chart of accounts *is* the
set of ledger accounts. Implementing both would duplicate the same
table. This module has ONE model, `LedgerAccount`, carrying every field
from both spec sections.

NOTE on integration: apps.expenses.LedgerPostingQueue and
apps.loans.LedgerPostingQueue already exist, built for exactly this.
This module's queue_consumer service reads pending rows from both and
posts real balanced journals — zero changes to those modules' files.
"""

import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class NormalBalance(models.TextChoices):
    DEBIT = "debit", "Debit"
    CREDIT = "credit", "Credit"


class AccountGroup(models.Model):
    """The 5 standard groups: Assets, Liabilities, Income, Expenses, Equity."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    family = models.ForeignKey(
        "families.Family", on_delete=models.CASCADE, related_name="account_groups"
    )
    name = models.CharField(max_length=50)
    normal_balance = models.CharField(max_length=10, choices=NormalBalance.choices)
    sort_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ledger_account_group"
        ordering = ["sort_order"]
        constraints = [
            models.UniqueConstraint(
                fields=["family", "name"], name="unique_account_group_per_family"
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.family_id})"


class LedgerAccountStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"


class LedgerAccount(models.Model):
    """Chart of Accounts entry — every Journal/Ledger entry posts against one of these."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    family = models.ForeignKey(
        "families.Family", on_delete=models.CASCADE, related_name="ledger_accounts"
    )
    account_code = models.CharField(max_length=20)
    account_name = models.CharField(max_length=150)
    account_group = models.ForeignKey(
        AccountGroup, on_delete=models.PROTECT, related_name="accounts"
    )
    parent_account = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="child_accounts"
    )
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=LedgerAccountStatus.choices, default=LedgerAccountStatus.ACTIVE
    )
    is_system_account = models.BooleanField(
        default=False, help_text="Seeded default account (Cash, Bank, ...) — cannot be deleted."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ledger_account"
        ordering = ["account_code"]
        constraints = [
            models.UniqueConstraint(
                fields=["family", "account_code"], name="unique_account_code_per_family"
            )
        ]
        indexes = [models.Index(fields=["family", "status"])]

    def __str__(self) -> str:
        return f"{self.account_code} — {self.account_name}"


class TransactionType(models.TextChoices):
    EXPENSE = "expense", "Expense"
    EXPENSE_SETTLEMENT = "expense_settlement", "Expense Settlement"
    INCOME = "income", "Income"
    LOAN_CREATION = "loan_creation", "Loan Creation"
    LOAN_PAYMENT = "loan_payment", "Loan Payment"
    BORROW = "borrow", "Borrow"
    LEND = "lend", "Lend"
    ADJUSTMENT = "adjustment", "Adjustment"
    OPENING_BALANCE = "opening_balance", "Opening Balance"
    MANUAL_JOURNAL = "manual_journal", "Manual Journal"


class JournalStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    POSTED = "posted", "Posted"
    REVERSED = "reversed", "Reversed"


def generate_journal_number() -> str:
    return f"JRN-{uuid.uuid4().hex[:10].upper()}"


class Journal(models.Model):
    """
    A balanced set of debit/credit lines (JournalEntry rows). Immutable
    once posted — corrections go through AdjustmentEntry, never an edit.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    journal_number = models.CharField(
        max_length=30, unique=True, default=generate_journal_number, editable=False
    )
    family = models.ForeignKey("families.Family", on_delete=models.CASCADE, related_name="journals")
    transaction_type = models.CharField(max_length=30, choices=TransactionType.choices)
    reference_type = models.CharField(
        max_length=50, blank=True, help_text="e.g. Expense, Loan, Settlement"
    )
    reference_id = models.CharField(max_length=64, blank=True)

    journal_date = models.DateField()
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=JournalStatus.choices, default=JournalStatus.DRAFT
    )

    created_by = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    posted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "ledger_journal"
        ordering = ["-journal_date", "-created_at"]
        indexes = [
            models.Index(fields=["family", "status"]),
            models.Index(fields=["transaction_type"]),
            models.Index(fields=["reference_type", "reference_id"]),
            models.Index(fields=["journal_number"]),
        ]

    def __str__(self) -> str:
        return f"{self.journal_number} ({self.status})"


class JournalEntryType(models.TextChoices):
    DEBIT = "debit", "Debit"
    CREDIT = "credit", "Credit"


class JournalEntry(models.Model):
    """One debit or credit line within a Journal. A Journal's lines must always balance."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name="entries")
    ledger_account = models.ForeignKey(
        LedgerAccount, on_delete=models.PROTECT, related_name="journal_entries"
    )
    entry_type = models.CharField(max_length=10, choices=JournalEntryType.choices)
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    description = models.CharField(max_length=255, blank=True)
    sequence = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "ledger_journal_entry"
        ordering = ["sequence"]
        indexes = [models.Index(fields=["journal"]), models.Index(fields=["ledger_account"])]

    def __str__(self) -> str:
        return f"{self.entry_type} {self.amount} — {self.ledger_account_id}"


def generate_ledger_number() -> str:
    return f"LDG-{uuid.uuid4().hex[:10].upper()}"


class LedgerEntry(models.Model):
    """
    The posted, immutable per-account record — one row per JournalEntry
    line, created only when a Journal is posted. Never edited or deleted
    after creation; a correction is a new LedgerEntry from an
    AdjustmentEntry's journal.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    ledger_number = models.CharField(
        max_length=30, unique=True, default=generate_ledger_number, editable=False
    )
    journal = models.ForeignKey(Journal, on_delete=models.PROTECT, related_name="ledger_entries")
    ledger_account = models.ForeignKey(
        LedgerAccount, on_delete=models.PROTECT, related_name="ledger_entries"
    )

    transaction_date = models.DateField()
    opening_balance = models.DecimalField(max_digits=14, decimal_places=2)
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    closing_balance = models.DecimalField(max_digits=14, decimal_places=2)

    reference_number = models.CharField(max_length=50, blank=True)
    remarks = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ledger_entry"
        ordering = ["transaction_date", "created_at"]
        indexes = [
            models.Index(fields=["ledger_account", "transaction_date"]),
            models.Index(fields=["journal"]),
            models.Index(fields=["ledger_number"]),
        ]

    def __str__(self) -> str:
        return f"{self.ledger_number} — {self.ledger_account_id}"


class AccountBalance(models.Model):
    """Current running totals per account — updated atomically on every posting."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    account = models.OneToOneField(LedgerAccount, on_delete=models.CASCADE, related_name="balance")
    opening_balance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    debit_total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    credit_total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    current_balance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))

    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ledger_account_balance"

    def __str__(self) -> str:
        return f"Balance({self.account_id}) = {self.current_balance}"


class OpeningBalance(models.Model):
    """Starting balance for an account within a FinancialPeriod."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    family = models.ForeignKey(
        "families.Family", on_delete=models.CASCADE, related_name="opening_balances"
    )
    ledger_account = models.ForeignKey(
        LedgerAccount, on_delete=models.CASCADE, related_name="opening_balances"
    )
    financial_period = models.ForeignKey(
        "FinancialPeriod", on_delete=models.CASCADE, related_name="opening_balances"
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    entry_type = models.CharField(max_length=10, choices=JournalEntryType.choices)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        db_table = "ledger_opening_balance"
        constraints = [
            models.UniqueConstraint(
                fields=["ledger_account", "financial_period"],
                name="unique_opening_balance_per_period",
            )
        ]

    def __str__(self) -> str:
        return f"Opening {self.amount} — {self.ledger_account_id} ({self.financial_period_id})"


class AdjustmentEntry(models.Model):
    """
    Tracks the link between a mistaken posting and its correction.
    Posted entries are never edited — this records why a correcting
    journal exists and what it corrects.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    family = models.ForeignKey(
        "families.Family", on_delete=models.CASCADE, related_name="adjustment_entries"
    )
    original_journal = models.ForeignKey(
        Journal,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="adjustments_against",
    )
    adjustment_journal = models.OneToOneField(
        Journal, on_delete=models.CASCADE, related_name="adjustment_record"
    )
    reason = models.TextField()

    created_by = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ledger_adjustment_entry"

    def __str__(self) -> str:
        return f"Adjustment {self.id} — {self.reason[:50]}"


class FinancialPeriodStatus(models.TextChoices):
    OPEN = "open", "Open"
    CLOSED = "closed", "Closed"


class FinancialPeriod(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    family = models.ForeignKey(
        "families.Family", on_delete=models.CASCADE, related_name="financial_periods"
    )
    name = models.CharField(max_length=100, help_text='e.g. "FY 2025-26" or "January 2026"')
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(
        max_length=20, choices=FinancialPeriodStatus.choices, default=FinancialPeriodStatus.OPEN
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ledger_financial_period"
        ordering = ["-start_date"]
        constraints = [
            models.UniqueConstraint(fields=["family", "name"], name="unique_period_name_per_family")
        ]
        indexes = [models.Index(fields=["family", "status"])]

    def __str__(self) -> str:
        return f"{self.name} ({self.status})"

    def contains(self, a_date) -> bool:
        return self.start_date <= a_date <= self.end_date


class ClosingPeriod(models.Model):
    """Records the act of closing a FinancialPeriod and the balances carried forward."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    family = models.ForeignKey(
        "families.Family", on_delete=models.CASCADE, related_name="closing_periods"
    )
    financial_period = models.OneToOneField(
        FinancialPeriod, on_delete=models.CASCADE, related_name="closing_record"
    )
    closing_balances_snapshot = models.JSONField(default=dict)

    closed_by = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    closed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ledger_closing_period"

    def __str__(self) -> str:
        return f"Closing of {self.financial_period_id}"
