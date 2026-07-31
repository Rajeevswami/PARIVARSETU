"""
Loan management models — internal family loans and external loans, with
installments, payments, configurable interest, and reminders.

NOTE on Ledger: this module has its own LedgerPostingQueue, separate
from the Expense module's. Each business domain queues its own posting
requests; a future Ledger Engine module consumes from all of them. See
apps.loans.services.ledger_hook.

NOTE on external parties: "lender" (Loan) is a nullable FK to Member for
internal loans, plus `external_lender_name` for external ones — no
separate contact-management model, since that's out of this module's
scope.
"""

import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class LoanTypeStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"


class LoanType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    family = models.ForeignKey(
        "families.Family", on_delete=models.CASCADE, related_name="loan_types"
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=LoanTypeStatus.choices, default=LoanTypeStatus.ACTIVE
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    updated_by = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    is_deleted = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = "loans_type"
        constraints = [
            models.UniqueConstraint(
                fields=["family", "name"], name="unique_loan_type_name_per_family"
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.family_id})"


class InterestType(models.TextChoices):
    NONE = "none", "None"
    SIMPLE = "simple", "Simple"
    COMPOUND = "compound", "Compound"


class LoanSource(models.TextChoices):
    INTERNAL = "internal", "Internal (family member)"
    EXTERNAL = "external", "External"


class LoanStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    RUNNING = "running", "Running"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"
    DEFAULTED = "defaulted", "Defaulted"


def generate_loan_number() -> str:
    return f"LOAN-{uuid.uuid4().hex[:10].upper()}"


class Loan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    loan_number = models.CharField(
        max_length=30, unique=True, default=generate_loan_number, editable=False
    )
    family = models.ForeignKey("families.Family", on_delete=models.CASCADE, related_name="loans")
    household = models.ForeignKey(
        "households.Household",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="loans",
    )

    borrower = models.ForeignKey(
        "members.Member", on_delete=models.PROTECT, related_name="loans_borrowed"
    )
    loan_source = models.CharField(
        max_length=20, choices=LoanSource.choices, default=LoanSource.INTERNAL
    )
    lender = models.ForeignKey(
        "members.Member", null=True, blank=True, on_delete=models.PROTECT, related_name="loans_lent"
    )
    external_lender_name = models.CharField(max_length=200, blank=True)

    loan_type = models.ForeignKey(
        LoanType, null=True, blank=True, on_delete=models.SET_NULL, related_name="loans"
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    principal_amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    interest_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0"), help_text="Annual percentage rate"
    )
    interest_type = models.CharField(
        max_length=20, choices=InterestType.choices, default=InterestType.NONE
    )
    interest_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    remaining_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))

    loan_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=LoanStatus.choices, default=LoanStatus.DRAFT)

    allow_overpayment = models.BooleanField(
        default=False,
        help_text="If off (default), a payment larger than the remaining balance is rejected.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    updated_by = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        db_table = "loans_loan"
        ordering = ["-loan_date", "-created_at"]
        indexes = [
            models.Index(fields=["family", "status"]),
            models.Index(fields=["borrower"]),
            models.Index(fields=["lender"]),
            models.Index(fields=["household"]),
            models.Index(fields=["loan_number"]),
            models.Index(fields=["due_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.loan_number} — {self.title} ({self.total_amount})"

    def soft_delete(self, deleted_by=None) -> None:
        from django.utils import timezone

        self.is_deleted = True
        self.status = LoanStatus.CANCELLED
        self.deleted_at = timezone.now()
        self.deleted_by = deleted_by
        self.save(update_fields=["is_deleted", "status", "deleted_at", "deleted_by"])


class InstallmentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PARTIAL = "partial", "Partially Paid"
    PAID = "paid", "Paid"
    OVERDUE = "overdue", "Overdue"


class LoanInstallment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="installments")
    installment_number = models.PositiveIntegerField()
    due_date = models.DateField()
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    status = models.CharField(
        max_length=20, choices=InstallmentStatus.choices, default=InstallmentStatus.PENDING
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "loans_installment"
        ordering = ["installment_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["loan", "installment_number"], name="unique_installment_number_per_loan"
            )
        ]
        indexes = [models.Index(fields=["loan", "status"]), models.Index(fields=["due_date"])]

    def __str__(self) -> str:
        return f"Installment {self.installment_number} of {self.loan_id}"


class LoanPaymentMethod(models.TextChoices):
    CASH = "cash", "Cash"
    BANK = "bank", "Bank"
    UPI = "upi", "UPI"
    CARD = "card", "Card"
    WALLET = "wallet", "Wallet"
    CHEQUE = "cheque", "Cheque"


def loan_payment_attachment_path(instance: "LoanPayment", filename: str) -> str:
    return f"loan_payment_attachments/{instance.loan_id}/{filename}"


def generate_payment_number() -> str:
    return f"PMT-{uuid.uuid4().hex[:10].upper()}"


class LoanPayment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="payments")
    installment = models.ForeignKey(
        LoanInstallment, null=True, blank=True, on_delete=models.SET_NULL, related_name="payments"
    )
    payment_number = models.CharField(
        max_length=30, unique=True, default=generate_payment_number, editable=False
    )
    payment_date = models.DateField()
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    interest_paid = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    principal_paid = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    remaining_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    payment_method = models.CharField(
        max_length=20, choices=LoanPaymentMethod.choices, default=LoanPaymentMethod.CASH
    )
    remarks = models.TextField(blank=True)
    attachment = models.FileField(upload_to=loan_payment_attachment_path, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        db_table = "loans_payment"
        ordering = ["-payment_date", "-created_at"]
        indexes = [models.Index(fields=["loan", "-payment_date"])]

    def __str__(self) -> str:
        return f"{self.payment_number} — {self.amount} on {self.loan_id}"


class CompoundingFrequency(models.TextChoices):
    MONTHLY = "monthly", "Monthly"
    QUARTERLY = "quarterly", "Quarterly"
    ANNUALLY = "annually", "Annually"


class InterestConfiguration(models.Model):
    """Reusable default interest settings a family can set once and apply to new loans."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    family = models.ForeignKey(
        "families.Family", on_delete=models.CASCADE, related_name="interest_configurations"
    )
    loan_type = models.ForeignKey(
        LoanType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="interest_configurations",
    )
    interest_type = models.CharField(
        max_length=20, choices=InterestType.choices, default=InterestType.SIMPLE
    )
    default_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0"))
    compounding_frequency = models.CharField(
        max_length=20, choices=CompoundingFrequency.choices, default=CompoundingFrequency.ANNUALLY
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "loans_interest_configuration"

    def __str__(self) -> str:
        return f"{self.get_interest_type_display()} @ {self.default_rate}% ({self.family_id})"


class ReminderType(models.TextChoices):
    DUE_DATE = "due_date", "Upcoming Due Date"
    OVERDUE = "overdue", "Overdue Loan"
    INSTALLMENT = "installment", "Pending Installment"
    CUSTOM = "custom", "Custom Reminder"


class ReminderStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    DISMISSED = "dismissed", "Dismissed"


class Reminder(models.Model):
    """
    Data record only — no delivery mechanism. A future Notifications
    module reads pending reminders and actually sends them; this module
    just creates and tracks them.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    family = models.ForeignKey(
        "families.Family", on_delete=models.CASCADE, related_name="loan_reminders"
    )
    loan = models.ForeignKey(
        Loan, null=True, blank=True, on_delete=models.CASCADE, related_name="reminders"
    )
    installment = models.ForeignKey(
        LoanInstallment, null=True, blank=True, on_delete=models.CASCADE, related_name="reminders"
    )
    member = models.ForeignKey(
        "members.Member", on_delete=models.CASCADE, related_name="loan_reminders"
    )

    reminder_type = models.CharField(
        max_length=20, choices=ReminderType.choices, default=ReminderType.CUSTOM
    )
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True)
    remind_at = models.DateTimeField()
    status = models.CharField(
        max_length=20, choices=ReminderStatus.choices, default=ReminderStatus.PENDING
    )

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        db_table = "loans_reminder"
        ordering = ["remind_at"]
        indexes = [
            models.Index(fields=["family", "status"]),
            models.Index(fields=["member", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} @ {self.remind_at}"


class LedgerPostingStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    POSTED = "posted", "Posted"


class LedgerPostingEvent(models.TextChoices):
    LOAN_CREATED = "loan_created", "Loan Created"
    LOAN_UPDATED = "loan_updated", "Loan Updated"
    LOAN_CANCELLED = "loan_cancelled", "Loan Cancelled"
    LOAN_PAYMENT_RECORDED = "loan_payment_recorded", "Loan Payment Recorded"
    BORROW_ENTRY = "borrow_entry", "Borrow Entry"
    LEND_ENTRY = "lend_entry", "Lend Entry"
    SETTLEMENT_RECORDED = "settlement_recorded", "Settlement Recorded"


class LedgerPostingQueue(models.Model):
    """
    Durable record of every ledger-posting obligation from Loan, Borrow,
    and Lend activity — nothing bypasses it. Actual General Ledger
    posting is the future Ledger Engine module's job. Separate from the
    Expense module's own queue by design (see module docstring).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    family = models.ForeignKey("families.Family", on_delete=models.CASCADE, related_name="+")
    event_type = models.CharField(max_length=30, choices=LedgerPostingEvent.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=20, choices=LedgerPostingStatus.choices, default=LedgerPostingStatus.PENDING
    )
    source_model = models.CharField(
        max_length=50, help_text="e.g. Loan, BorrowTransaction, LendTransaction"
    )
    source_id = models.CharField(max_length=64)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "loans_ledger_posting_queue"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["family", "status"])]

    def __str__(self) -> str:
        return f"{self.event_type} — {self.amount} ({self.status})"
