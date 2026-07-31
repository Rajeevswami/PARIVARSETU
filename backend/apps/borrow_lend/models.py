"""
Borrow/Lend models — simpler, interest-free cousin of Loan: a single
transaction record plus a generic Settlement model shared by both
BorrowTransaction and LendTransaction (reference_type/reference_id,
not a GenericForeignKey — consistent with the project's explicit-FK
style elsewhere).

Loans (apps.loans) use LoanPayment for their richer principal/interest
breakdown; Settlement here is intentionally simpler since Borrow/Lend
carry no interest.
"""

import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class TransactionPaymentMethod(models.TextChoices):
    CASH = "cash", "Cash"
    BANK = "bank", "Bank"
    UPI = "upi", "UPI"
    CARD = "card", "Card"
    WALLET = "wallet", "Wallet"
    CHEQUE = "cheque", "Cheque"


class TransactionStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PARTIALLY_SETTLED = "partially_settled", "Partially Settled"
    SETTLED = "settled", "Settled"
    CANCELLED = "cancelled", "Cancelled"


def generate_transaction_number(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10].upper()}"


def generate_borrow_number() -> str:
    return generate_transaction_number("BRW")


def generate_lend_number() -> str:
    return generate_transaction_number("LND")


class BorrowTransaction(models.Model):
    """A family member borrowed money — from another member, or an external party."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    transaction_number = models.CharField(
        max_length=30, unique=True, default=generate_borrow_number, editable=False
    )
    family = models.ForeignKey(
        "families.Family", on_delete=models.CASCADE, related_name="borrow_transactions"
    )
    household = models.ForeignKey(
        "households.Household",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="borrow_transactions",
    )

    borrower = models.ForeignKey(
        "members.Member", on_delete=models.PROTECT, related_name="amounts_borrowed"
    )
    lender = models.ForeignKey(
        "members.Member",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="amounts_lent_to_others",
    )
    external_lender_name = models.CharField(max_length=200, blank=True)

    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    date = models.DateField()
    reason = models.TextField(blank=True)
    payment_method = models.CharField(
        max_length=20,
        choices=TransactionPaymentMethod.choices,
        default=TransactionPaymentMethod.CASH,
    )
    status = models.CharField(
        max_length=20, choices=TransactionStatus.choices, default=TransactionStatus.PENDING
    )
    settled_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))

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
        db_table = "borrow_lend_borrow_transaction"
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["family", "status"]),
            models.Index(fields=["borrower"]),
            models.Index(fields=["household"]),
        ]

    def __str__(self) -> str:
        return f"{self.transaction_number} — {self.amount}"

    @property
    def remaining_amount(self) -> Decimal:
        return self.amount - self.settled_amount


class LendTransaction(models.Model):
    """A family member lent money — to another member, or an external party."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    transaction_number = models.CharField(
        max_length=30, unique=True, default=generate_lend_number, editable=False
    )
    family = models.ForeignKey(
        "families.Family", on_delete=models.CASCADE, related_name="lend_transactions"
    )
    household = models.ForeignKey(
        "households.Household",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="lend_transactions",
    )

    giver = models.ForeignKey(
        "members.Member", on_delete=models.PROTECT, related_name="amounts_given"
    )
    receiver = models.ForeignKey(
        "members.Member",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="amounts_received",
    )
    external_receiver_name = models.CharField(max_length=200, blank=True)

    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    date = models.DateField()
    reason = models.TextField(blank=True)
    payment_method = models.CharField(
        max_length=20,
        choices=TransactionPaymentMethod.choices,
        default=TransactionPaymentMethod.CASH,
    )
    status = models.CharField(
        max_length=20, choices=TransactionStatus.choices, default=TransactionStatus.PENDING
    )
    settled_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))

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
        db_table = "borrow_lend_lend_transaction"
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["family", "status"]),
            models.Index(fields=["giver"]),
            models.Index(fields=["household"]),
        ]

    def __str__(self) -> str:
        return f"{self.transaction_number} — {self.amount}"

    @property
    def remaining_amount(self) -> Decimal:
        return self.amount - self.settled_amount


class SettlementReferenceType(models.TextChoices):
    BORROW = "borrow", "Borrow Transaction"
    LEND = "lend", "Lend Transaction"


class SettlementStatus(models.TextChoices):
    RECORDED = "recorded", "Recorded"
    REVERSED = "reversed", "Reversed"


class Settlement(models.Model):
    """
    Generic settlement record for BorrowTransaction/LendTransaction —
    reference_type + reference_id instead of a GenericForeignKey, so it
    stays queryable with plain FKs elsewhere in the codebase.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    reference_type = models.CharField(max_length=20, choices=SettlementReferenceType.choices)
    reference_id = models.UUIDField()
    member = models.ForeignKey(
        "members.Member", on_delete=models.CASCADE, related_name="settlements_made"
    )

    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    settled_amount = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="Cumulative total settled after this event"
    )
    remaining_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=20, choices=SettlementStatus.choices, default=SettlementStatus.RECORDED
    )
    settlement_date = models.DateField()
    remarks = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        db_table = "borrow_lend_settlement"
        ordering = ["-settlement_date", "-created_at"]
        indexes = [models.Index(fields=["reference_type", "reference_id"])]

    def __str__(self) -> str:
        return f"Settlement {self.id} on {self.reference_type}:{self.reference_id}"
