"""
Expense management models.

NOTE on "EXPENSE TYPES" (Personal, Household, Medical, Education, ...):
these are implemented as default ExpenseCategory rows seeded per-family
(see signals.py), not a separate field on Expense — ExpenseCategory
already is the categorization mechanism, and a family can rename/reorder/
deactivate/add its own categories from there.

NOTE on Ledger: every Expense/Settlement writes to LedgerPostingQueue
(see below) — nothing bypasses it. This module does not implement the
actual General Ledger posting logic; that's the future Ledger Engine
module's job. The queue is fully functional today: it durably records
every posting request awaiting that module.
"""

import hashlib
import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class ExpenseCategoryStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"


class ExpenseCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    family = models.ForeignKey(
        "families.Family", on_delete=models.CASCADE, related_name="expense_categories"
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="lucide-react icon name")
    color = models.CharField(max_length=7, default="#64748b", help_text="Hex color, e.g. #64748b")
    sort_order = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=20, choices=ExpenseCategoryStatus.choices, default=ExpenseCategoryStatus.ACTIVE
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
        db_table = "expenses_category"
        verbose_name_plural = "Expense Categories"
        ordering = ["sort_order", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["family", "name"], name="unique_category_name_per_family"
            )
        ]
        indexes = [models.Index(fields=["family", "status"])]

    def __str__(self) -> str:
        return f"{self.name} ({self.family_id})"


class ExpensePaymentMethod(models.TextChoices):
    CASH = "cash", "Cash"
    BANK = "bank", "Bank"
    UPI = "upi", "UPI"
    CARD = "card", "Card"
    WALLET = "wallet", "Wallet"
    CHEQUE = "cheque", "Cheque"


class ExpenseVisibility(models.TextChoices):
    PRIVATE = "private", "Private"
    HOUSEHOLD = "household", "Household"
    FAMILY = "family", "Entire Family"


class ExpenseStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    SETTLED = "settled", "Settled"
    CANCELLED = "cancelled", "Cancelled"


def generate_expense_number() -> str:
    return f"EXP-{uuid.uuid4().hex[:10].upper()}"


class Expense(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    expense_number = models.CharField(
        max_length=30, unique=True, default=generate_expense_number, editable=False
    )
    family = models.ForeignKey("families.Family", on_delete=models.CASCADE, related_name="expenses")
    household = models.ForeignKey(
        "households.Household",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="expenses",
    )
    category = models.ForeignKey(
        ExpenseCategory, null=True, blank=True, on_delete=models.SET_NULL, related_name="expenses"
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    expense_date = models.DateField()
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    currency = models.CharField(max_length=3, default="INR")

    paid_by = models.ForeignKey(
        "members.Member", on_delete=models.PROTECT, related_name="expenses_paid"
    )
    payment_method = models.CharField(
        max_length=20, choices=ExpensePaymentMethod.choices, default=ExpensePaymentMethod.CASH
    )
    visibility = models.CharField(
        max_length=20, choices=ExpenseVisibility.choices, default=ExpenseVisibility.HOUSEHOLD
    )
    status = models.CharField(
        max_length=20, choices=ExpenseStatus.choices, default=ExpenseStatus.PENDING
    )

    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

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
        db_table = "expenses_expense"
        ordering = ["-expense_date", "-created_at"]
        indexes = [
            models.Index(fields=["family", "status"]),
            models.Index(fields=["household"]),
            models.Index(fields=["paid_by"]),
            models.Index(fields=["category"]),
            models.Index(fields=["expense_date"]),
            models.Index(fields=["expense_number"]),
        ]

    def __str__(self) -> str:
        return f"{self.expense_number} — {self.title} ({self.amount} {self.currency})"

    def soft_delete(self, deleted_by=None) -> None:
        from django.utils import timezone

        self.is_deleted = True
        self.status = ExpenseStatus.CANCELLED
        self.deleted_at = timezone.now()
        self.deleted_by = deleted_by
        self.save(update_fields=["is_deleted", "status", "deleted_at", "deleted_by"])


class ExpenseParticipantStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PARTIALLY_SETTLED = "partially_settled", "Partially Settled"
    SETTLED = "settled", "Settled"


class ExpenseParticipant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name="participants")
    member = models.ForeignKey(
        "members.Member", on_delete=models.CASCADE, related_name="expense_shares"
    )

    share_amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0"))]
    )
    share_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    settled_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    pending_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    status = models.CharField(
        max_length=20,
        choices=ExpenseParticipantStatus.choices,
        default=ExpenseParticipantStatus.PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "expenses_participant"
        constraints = [
            models.UniqueConstraint(
                fields=["expense", "member"], name="unique_participant_per_expense"
            )
        ]
        indexes = [models.Index(fields=["expense", "status"]), models.Index(fields=["member"])]

    def __str__(self) -> str:
        return f"{self.member_id} owes {self.pending_amount} on {self.expense_id}"

    def recompute(self, save: bool = True) -> None:
        self.pending_amount = self.share_amount - self.settled_amount
        if self.settled_amount <= 0:
            self.status = ExpenseParticipantStatus.PENDING
        elif self.pending_amount <= 0:
            self.status = ExpenseParticipantStatus.SETTLED
        else:
            self.status = ExpenseParticipantStatus.PARTIALLY_SETTLED
        if save:
            self.save(update_fields=["pending_amount", "status", "updated_at"])


def attachment_upload_path(instance: "ExpenseAttachment", filename: str) -> str:
    return f"expense_attachments/{instance.expense_id}/{filename}"


class ExpenseAttachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to=attachment_upload_path)
    file_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100, blank=True)
    file_size = models.PositiveIntegerField(default=0)
    checksum = models.CharField(max_length=64, blank=True, help_text="SHA-256 of the file content")
    uploaded_by = models.ForeignKey(
        "accounts.User", null=True, on_delete=models.SET_NULL, related_name="+"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "expenses_attachment"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["expense"])]

    def __str__(self) -> str:
        return f"{self.file_name} ({self.expense_id})"

    @staticmethod
    def compute_checksum(file_obj) -> str:
        hasher = hashlib.sha256()
        for chunk in file_obj.chunks():
            hasher.update(chunk)
        file_obj.seek(0)
        return hasher.hexdigest()


class ExpenseComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name="comments")
    member = models.ForeignKey(
        "members.Member", on_delete=models.CASCADE, related_name="expense_comments"
    )
    comment = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "expenses_comment"
        ordering = ["created_at"]
        indexes = [models.Index(fields=["expense", "created_at"])]

    def __str__(self) -> str:
        return f"Comment by {self.member_id} on {self.expense_id}"


class ExpenseSettlementStatus(models.TextChoices):
    RECORDED = "recorded", "Recorded"
    REVERSED = "reversed", "Reversed"


class ExpenseSettlement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name="settlements")
    member = models.ForeignKey(
        "members.Member", on_delete=models.CASCADE, related_name="expense_settlements"
    )

    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    received_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    remaining_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    settlement_date = models.DateField()
    remarks = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=ExpenseSettlementStatus.choices,
        default=ExpenseSettlementStatus.RECORDED,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        db_table = "expenses_settlement"
        ordering = ["-settlement_date", "-created_at"]
        indexes = [models.Index(fields=["expense", "member"]), models.Index(fields=["status"])]

    def __str__(self) -> str:
        return f"Settlement {self.id} for {self.expense_id}"


class LedgerPostingStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    POSTED = "posted", "Posted"


class LedgerPostingEvent(models.TextChoices):
    EXPENSE_CREATED = "expense_created", "Expense Created"
    EXPENSE_UPDATED = "expense_updated", "Expense Updated"
    EXPENSE_CANCELLED = "expense_cancelled", "Expense Cancelled"
    SETTLEMENT_RECORDED = "settlement_recorded", "Settlement Recorded"


class LedgerPostingQueue(models.Model):
    """
    Durable record of every ledger-posting obligation this module creates.
    Every Expense create/update/cancel and every Settlement writes here —
    nothing bypasses it. The actual General Ledger posting (turning these
    into journal entries) is the future Ledger Engine module's job; this
    queue is what it will consume. Kept inside apps.expenses (not
    apps.ledger) since the Ledger Engine app itself is out of scope here.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    family = models.ForeignKey("families.Family", on_delete=models.CASCADE, related_name="+")
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name="ledger_postings")
    event_type = models.CharField(max_length=30, choices=LedgerPostingEvent.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=20, choices=LedgerPostingStatus.choices, default=LedgerPostingStatus.PENDING
    )
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "expenses_ledger_posting_queue"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["family", "status"])]

    def __str__(self) -> str:
        return f"{self.event_type} — {self.amount} ({self.status})"
