"""
Family model — the top-level tenant boundary for the whole application.
Every Household and Member belongs to exactly one Family; every future
business module (expenses, loans, ledger, ...) scopes its data by
family_id.
"""

import secrets
import uuid

from django.db import models


class SubscriptionPlan(models.TextChoices):
    FREE = "free", "Free"
    BASIC = "basic", "Basic"
    PREMIUM = "premium", "Premium"
    ENTERPRISE = "enterprise", "Enterprise"


class SubscriptionStatus(models.TextChoices):
    TRIAL = "trial", "Trial"
    ACTIVE = "active", "Active"
    PAST_DUE = "past_due", "Past Due"
    CANCELLED = "cancelled", "Cancelled"
    EXPIRED = "expired", "Expired"


class FamilyStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    SUSPENDED = "suspended", "Suspended"


def family_logo_path(instance: "Family", filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    return f"family_logos/{instance.id}.{ext}"


def generate_family_code() -> str:
    return f"FAM-{secrets.token_hex(4).upper()}"


class Family(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    family_name = models.CharField(max_length=150)
    family_code = models.CharField(
        max_length=20, unique=True, default=generate_family_code, editable=False
    )
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to=family_logo_path, null=True, blank=True)

    country = models.CharField(max_length=100, default="India")
    state = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    currency = models.CharField(max_length=3, default="INR")
    language = models.CharField(max_length=10, default="en")
    timezone = models.CharField(max_length=50, default="Asia/Kolkata")

    subscription_plan = models.CharField(
        max_length=20, choices=SubscriptionPlan.choices, default=SubscriptionPlan.FREE
    )
    subscription_status = models.CharField(
        max_length=20, choices=SubscriptionStatus.choices, default=SubscriptionStatus.TRIAL
    )
    status = models.CharField(
        max_length=20, choices=FamilyStatus.choices, default=FamilyStatus.ACTIVE
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="families_created",
    )
    updated_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="families_updated",
    )
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="families_deleted",
    )

    class Meta:
        db_table = "families_family"
        verbose_name = "Family"
        verbose_name_plural = "Families"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "is_deleted"]),
            models.Index(fields=["family_code"]),
        ]

    def __str__(self) -> str:
        return f"{self.family_name} ({self.family_code})"

    def soft_delete(self, deleted_by=None) -> None:
        from django.utils import timezone

        self.is_deleted = True
        self.status = FamilyStatus.INACTIVE
        self.deleted_at = timezone.now()
        self.deleted_by = deleted_by
        self.save(update_fields=["is_deleted", "status", "deleted_at", "deleted_by"])
